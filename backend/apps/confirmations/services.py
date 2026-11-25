"""Business logic services for Public Dealer Date Confirmation & Link Validation."""
from datetime import date

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import status

from apps.audit_logs.services import log_audit_event
from apps.notifications.services import on_form_submitted
from apps.confirmations.models import (
    Confirmation,
    ConfirmationHistory,
    ConfirmationHistoryAction,
    ConfirmationLink,
    ConfirmationLinkStatus,
    ConfirmationStatus,
)
from apps.scheduling.models import BlockedSlot, Holiday, TimeSlot
from apps.scheduling.selectors import (
    get_active_time_slots,
    get_allow_same_day_booking,
    get_authoritative_today,
    get_available_slots_for_date,
    get_eligible_dates_for_allowed_month,
)
from common.exceptions.domain import ConflictError, DomainError, NotFoundError
from common.validators.mobile import normalize_dealer_code, normalize_indian_mobile
from services.tokens import hash_token

APPROVED_SUCCESS_MESSAGE = (
    "Thank You, Your Confirmation form are submited successfully. "
    "If you want to change date and time so please connect to your RM."
)


def _resolve_and_validate_public_link(raw_token: str, *, lock: bool = False) -> ConfirmationLink:
    """Lookup confirmation link by SHA-256 hash and enforce lifecycle status & expiry."""
    token_hash = hash_token(raw_token)
    qs = ConfirmationLink.objects.select_related("dealer", "campaign")
    if lock:
        qs = qs.select_for_update()

    link = qs.filter(token_hash=token_hash).first()
    if link is None:
        raise NotFoundError(
            message="Invalid confirmation link. Please check the URL or contact your RM.",
            code="INVALID_CONFIRMATION_TOKEN",
        )

    if link.status == ConfirmationLinkStatus.DEACTIVATED:
        raise DomainError(
            message="This confirmation link has been deactivated. Please connect with your RM.",
            code="LINK_DEACTIVATED",
            status_code=status.HTTP_410_GONE,
        )

    if link.status == ConfirmationLinkStatus.USED or link.submission_count >= link.max_submissions:
        raise ConflictError(
            message="Your confirmation has already been submitted. If you want to change date and time, please connect to your RM.",
            code="DUPLICATE_SUBMISSION",
        )

    if link.status == ConfirmationLinkStatus.EXPIRED or link.is_expired:
        if link.status != ConfirmationLinkStatus.EXPIRED:
            link.status = ConfirmationLinkStatus.EXPIRED
            link.save(update_fields=["status", "updated_at"])
        raise DomainError(
            message="This confirmation link has expired. Please request a new link from your RM.",
            code="LINK_EXPIRED",
            status_code=status.HTTP_410_GONE,
        )

    return link


def get_public_link_metadata(*, raw_token: str, today_override: date | None = None) -> dict:
    """Return safe public metadata (zero internal DB IDs) and eligible dates in allowed_month."""
    link = _resolve_and_validate_public_link(raw_token, lock=False)
    tz_name = link.campaign.timezone or "Asia/Kolkata"
    available_dates = get_eligible_dates_for_allowed_month(
        allowed_month=link.allowed_month,
        tz_name=tz_name,
        today_override=today_override,
    )
    return {
        "dealer_code": link.dealer.dealer_code,
        "mobile_number": link.dealer.mobile_number,
        "campaign_name": link.campaign.campaign_name,
        "allowed_month": link.allowed_month,
        "timezone": tz_name,
        "expires_at": link.expires_at,
        "available_dates": available_dates,
        "has_available_dates": len(available_dates) > 0,
        "default_slots": get_active_time_slots(),
    }


def validate_date_for_link(
    *,
    link: ConfirmationLink,
    selected_date: date,
    today_override: date | None = None,
) -> None:
    """Enforce authoritative same-month future-only date rule and holiday check."""
    tz_name = link.campaign.timezone or "Asia/Kolkata"
    today = today_override or get_authoritative_today(tz_name)
    allow_same_day = get_allow_same_day_booking()

    selected_month = f"{selected_date.year:04d}-{selected_date.month:02d}"
    if selected_month != link.allowed_month:
        raise DomainError(
            message="You can only select dates within the month in which your confirmation link was issued.",
            code="DATE_OUTSIDE_ALLOWED_MONTH",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"preferred_date": ["Selected date is outside the allowed calendar month."]},
        )

    if allow_same_day:
        if selected_date < today:
            raise DomainError(
                message="Past dates cannot be selected. Please choose an upcoming date.",
                code="PAST_DATE_NOT_ALLOWED",
                status_code=status.HTTP_400_BAD_REQUEST,
                details={"preferred_date": ["Past dates are not allowed."]},
            )
    else:
        if selected_date <= today:
            raise DomainError(
                message="Please select a future date within this month.",
                code="PAST_DATE_NOT_ALLOWED",
                status_code=status.HTTP_400_BAD_REQUEST,
                details={"preferred_date": ["Only future dates within the allowed month can be selected."]},
            )

    if Holiday.objects.filter(date=selected_date, is_active=True).exists():
        raise DomainError(
            message="The selected date is a holiday and is unavailable for booking.",
            code="DATE_IS_HOLIDAY",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"preferred_date": ["Selected date is a holiday."]},
        )


def get_public_date_availability(
    *,
    raw_token: str,
    target_date: date,
    today_override: date | None = None,
) -> dict:
    """Return available 1-hour time slots for a validated date on a valid link."""
    link = _resolve_and_validate_public_link(raw_token, lock=False)
    validate_date_for_link(link=link, selected_date=target_date, today_override=today_override)
    slots = get_available_slots_for_date(target_date)
    return {
        "date": target_date.isoformat(),
        "slots": slots,
    }


@transaction.atomic
def submit_public_confirmation(
    *,
    raw_token: str,
    dealer_code: str,
    mobile_number: str,
    preferred_date: date,
    preferred_time_slot_id,
    today_override: date | None = None,
) -> dict:
    """
    Concurrency-safe atomic dealer confirmation submission:
    1. Lock ConfirmationLink row (prevents duplicate submissions).
    2. Validate dealer_code & 10-digit mobile_number against link.dealer.
    3. Validate preferred_date against allowed_month + authoritative today + holidays.
    4. Lock TimeSlot row (prevents concurrent overbooking beyond max_capacity).
    5. Create Confirmation + ConfirmationHistory + update link status + write AuditLog.
    """
    link = _resolve_and_validate_public_link(raw_token, lock=True)

    # Verify dealer code & mobile number against linked dealer
    normalized_code = normalize_dealer_code(dealer_code)
    if normalized_code != link.dealer.dealer_code:
        raise DomainError(
            message="Invalid Dealer Code. Please enter the exact Dealer Code registered with Havells.",
            code="INVALID_DEALER_CODE",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"dealer_code": ["Dealer Code does not match this confirmation link."]},
        )

    normalized_mobile = normalize_indian_mobile(mobile_number)
    if normalized_mobile != link.dealer.mobile_number:
        raise DomainError(
            message="Mobile number does not match our registered dealer record.",
            code="MOBILE_NUMBER_MISMATCH",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"mobile_number": ["Mobile number does not match the registered dealer."]},
        )

    # Validate date against same-month future-only rule & holidays
    validate_date_for_link(link=link, selected_date=preferred_date, today_override=today_override)

    # Lock TimeSlot row for atomic capacity check
    time_slot = (
        TimeSlot.objects.select_for_update()
        .filter(id=preferred_time_slot_id, is_active=True)
        .first()
    )
    if time_slot is None:
        raise DomainError(
            message="Selected time slot is invalid or inactive. Please select an available time slot.",
            code="TIME_SLOT_UNAVAILABLE",
            status_code=status.HTTP_409_CONFLICT,
            details={"preferred_time_slot": ["Time slot is unavailable."]},
        )

    if BlockedSlot.objects.filter(date=preferred_date, time_slot=time_slot, is_active=True).exists():
        raise ConflictError(
            message="The selected time slot is currently unavailable. Please choose another slot.",
            code="TIME_SLOT_UNAVAILABLE",
            details={"preferred_time_slot": ["Selected time slot is blocked for this date."]},
        )

    active_bookings = Confirmation.objects.filter(
        preferred_date=preferred_date,
        preferred_time_slot=time_slot,
        submission_status=ConfirmationStatus.CONFIRMED,
    ).count()

    if active_bookings >= time_slot.max_capacity:
        raise ConflictError(
            message="The selected time slot is no longer available. Please choose another slot.",
            code="TIME_SLOT_UNAVAILABLE",
            details={"preferred_time_slot": ["Selected time slot has reached maximum capacity."]},
        )

    try:
        confirmation = Confirmation.objects.create(
            dealer=link.dealer,
            confirmation_link=link,
            campaign=link.campaign,
            preferred_date=preferred_date,
            preferred_time_slot=time_slot,
            submission_status=ConfirmationStatus.CONFIRMED,
            submitted_at=timezone.now(),
        )
    except IntegrityError as exc:
        raise ConflictError(
            message="Your confirmation has already been submitted.",
            code="DUPLICATE_SUBMISSION",
        ) from exc

    ConfirmationHistory.objects.create(
        confirmation=confirmation,
        action=ConfirmationHistoryAction.CREATED,
        new_date=preferred_date,
        new_time_slot=time_slot,
        reason="Submitted by dealer via public confirmation link.",
    )

    link.submission_count += 1
    if link.shared_at is None:
        link.shared_at = timezone.now()
    if link.submission_count >= link.max_submissions:
        link.status = ConfirmationLinkStatus.USED
    link.save(update_fields=["submission_count", "shared_at", "status", "updated_at"])

    log_audit_event(
        user=None,
        action="DEALER_CONFIRMATION_SUBMITTED",
        module="confirmations",
        object_type="Confirmation",
        object_id=str(confirmation.id),
        new_values={
            "dealer_code": link.dealer.dealer_code,
            "campaign_code": link.campaign.campaign_code,
            "preferred_date": preferred_date.isoformat(),
            "preferred_time_slot": time_slot.display_label,
        },
    )
    on_form_submitted(confirmation=confirmation)

    return {
        "dealer_code": link.dealer.dealer_code,
        "preferred_date": preferred_date.isoformat(),
        "preferred_time_slot": time_slot.display_label,
        "submitted_at": confirmation.submitted_at,
        "confirmation_message": APPROVED_SUCCESS_MESSAGE,
    }
