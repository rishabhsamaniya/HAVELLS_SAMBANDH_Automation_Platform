"""Scheduling service helpers: operating hours, slot generation, holidays, blocking, manual booking, reschedule & cancel."""
from datetime import date, datetime, time, timedelta

from django.db import transaction
from django.db.models import Count
from django.utils import timezone
from rest_framework import status

from apps.accounts.models import User
from apps.audit_logs.services import log_audit_event
from apps.notifications.services import on_booking_changed
from apps.campaigns.models import Campaign
from apps.confirmations.models import (
    Confirmation,
    ConfirmationHistory,
    ConfirmationHistoryAction,
    ConfirmationStatus,
)
from apps.dealers.models import Dealer, DealerStatus
from apps.scheduling.models import BlockedSlot, Holiday, OperatingHoursConfig, TimeSlot
from common.exceptions.domain import ConflictError, DomainError


@transaction.atomic
def generate_time_slots_from_config(config: OperatingHoursConfig | None = None) -> list[TimeSlot]:
    """Generate or activate time slots from OperatingHoursConfig (default 24 hours: 00:00-00:00, 60 min)."""
    if config is None:
        config = OperatingHoursConfig.objects.filter(is_active=True).first()
    if config is None:
        config = OperatingHoursConfig.objects.create(
            opening_time=time(0, 0),
            closing_time=time(0, 0),
            slot_duration=60,
            default_capacity=1,
            allow_same_day_booking=False,
            is_active=True,
        )

    base_day = datetime(2026, 1, 1)
    cursor = datetime.combine(base_day.date(), config.opening_time)
    if config.closing_time == time(0, 0):
        closing = datetime.combine(base_day.date() + timedelta(days=1), time(0, 0))
    else:
        closing = datetime.combine(base_day.date(), config.closing_time)
    step = timedelta(minutes=config.slot_duration)

    slots = []
    while cursor + step <= closing:
        slot_start = cursor.time()
        slot_end = (cursor + step).time()
        slot, created = TimeSlot.objects.get_or_create(
            start_time=slot_start,
            end_time=slot_end,
            defaults={
                "slot_duration": config.slot_duration,
                "max_capacity": config.default_capacity,
                "is_active": True,
            },
        )
        if not created and not slot.is_active:
            slot.is_active = True
            slot.save(update_fields=["is_active", "updated_at"])
        slots.append(slot)
        cursor += step

    return slots


@transaction.atomic
def update_operating_hours(*, actor: User, validated_data: dict) -> OperatingHoursConfig:
    config = OperatingHoursConfig.objects.filter(is_active=True).first()
    if config is None:
        config = OperatingHoursConfig.objects.create(**validated_data, is_active=True)
    else:
        for field, value in validated_data.items():
            setattr(config, field, value)
        config.save()

    generate_time_slots_from_config(config)
    log_audit_event(
        user=actor,
        action="OPERATING_HOURS_UPDATED",
        module="scheduling",
        object_type="OperatingHoursConfig",
        object_id=str(config.id),
        new_values={
            "opening_time": config.opening_time.strftime("%H:%M"),
            "closing_time": config.closing_time.strftime("%H:%M"),
            "slot_duration": config.slot_duration,
            "default_capacity": config.default_capacity,
            "allow_same_day_booking": config.allow_same_day_booking,
        },
    )
    return config


def get_internal_date_availability(*, target_date: date) -> dict:
    """Detailed internal slot breakdown for admins/RMs (includes booked, remaining, blocked, holiday)."""
    holiday = Holiday.objects.filter(date=target_date, is_active=True).first()
    blocked_map = {
        b.time_slot_id: b
        for b in BlockedSlot.objects.filter(date=target_date, is_active=True)
    }
    booked_counts = dict(
        Confirmation.objects.filter(
            preferred_date=target_date,
            submission_status=ConfirmationStatus.CONFIRMED,
        )
        .values("preferred_time_slot_id")
        .annotate(booked=Count("id"))
        .values_list("preferred_time_slot_id", "booked")
    )

    slots_data = []
    for slot in TimeSlot.objects.all().order_by("start_time"):
        booked = booked_counts.get(slot.id, 0)
        blocked = blocked_map.get(slot.id)
        remaining = 0 if (holiday or blocked or not slot.is_active) else max(0, slot.max_capacity - booked)
        slots_data.append(
            {
                "id": str(slot.id),
                "label": slot.display_label,
                "start_time": slot.start_time.strftime("%H:%M"),
                "end_time": slot.end_time.strftime("%H:%M"),
                "max_capacity": slot.max_capacity,
                "booked_count": booked,
                "remaining_capacity": remaining,
                "is_active": slot.is_active,
                "is_blocked": blocked is not None,
                "blocked_reason": blocked.reason if blocked else "",
            }
        )

    return {
        "date": target_date.isoformat(),
        "is_holiday": holiday is not None,
        "holiday_name": holiday.name if holiday else None,
        "slots": slots_data,
    }


def _validate_and_lock_slot_for_date(*, target_date: date, time_slot_id, exclude_confirmation_id=None) -> TimeSlot:
    if Holiday.objects.filter(date=target_date, is_active=True).exists():
        raise DomainError(
            message="The selected date is a holiday and cannot be booked.",
            code="DATE_IS_HOLIDAY",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    time_slot = (
        TimeSlot.objects.select_for_update()
        .filter(id=time_slot_id, is_active=True)
        .first()
    )
    if time_slot is None:
        raise ConflictError(
            message="Selected time slot is invalid or inactive.",
            code="TIME_SLOT_UNAVAILABLE",
        )

    if BlockedSlot.objects.filter(date=target_date, time_slot=time_slot, is_active=True).exists():
        raise ConflictError(
            message="Selected time slot is blocked for this date.",
            code="TIME_SLOT_UNAVAILABLE",
        )

    qs = Confirmation.objects.filter(
        preferred_date=target_date,
        preferred_time_slot=time_slot,
        submission_status=ConfirmationStatus.CONFIRMED,
    )
    if exclude_confirmation_id is not None:
        qs = qs.exclude(id=exclude_confirmation_id)

    if qs.count() >= time_slot.max_capacity:
        raise ConflictError(
            message="Selected time slot has reached maximum capacity.",
            code="TIME_SLOT_UNAVAILABLE",
        )

    return time_slot


@transaction.atomic
def create_manual_booking(
    *,
    actor: User,
    dealer: Dealer,
    campaign: Campaign,
    preferred_date: date,
    preferred_time_slot_id,
    reason: str = "Manual booking created by internal team.",
) -> Confirmation:
    if dealer.status != DealerStatus.ACTIVE:
        raise DomainError(
            message="Cannot book a slot for an inactive dealer.",
            code="DEALER_INACTIVE",
        )

    time_slot = _validate_and_lock_slot_for_date(
        target_date=preferred_date,
        time_slot_id=preferred_time_slot_id,
    )

    confirmation = Confirmation.objects.create(
        dealer=dealer,
        campaign=campaign,
        preferred_date=preferred_date,
        preferred_time_slot=time_slot,
        submission_status=ConfirmationStatus.CONFIRMED,
        submitted_at=timezone.now(),
        created_by=actor,
    )

    ConfirmationHistory.objects.create(
        confirmation=confirmation,
        action=ConfirmationHistoryAction.CREATED,
        new_date=preferred_date,
        new_time_slot=time_slot,
        reason=reason,
        changed_by=actor,
    )

    log_audit_event(
        user=actor,
        action="MANUAL_BOOKING_CREATED",
        module="scheduling",
        object_type="Confirmation",
        object_id=str(confirmation.id),
        new_values={
            "dealer_code": dealer.dealer_code,
            "preferred_date": preferred_date.isoformat(),
            "preferred_time_slot": time_slot.display_label,
        },
    )
    return confirmation


@transaction.atomic
def reschedule_booking(
    *,
    actor: User,
    confirmation: Confirmation,
    new_date: date,
    new_time_slot_id,
    reason: str = "",
) -> Confirmation:
    if confirmation.submission_status == ConfirmationStatus.CANCELLED:
        raise DomainError(
            message="Cannot reschedule a cancelled booking.",
            code="BOOKING_ALREADY_CANCELLED",
        )

    prev_date = confirmation.preferred_date
    prev_slot = confirmation.preferred_time_slot

    new_slot = _validate_and_lock_slot_for_date(
        target_date=new_date,
        time_slot_id=new_time_slot_id,
        exclude_confirmation_id=confirmation.id,
    )

    confirmation.preferred_date = new_date
    confirmation.preferred_time_slot = new_slot
    confirmation.submission_status = ConfirmationStatus.CONFIRMED
    confirmation.save(update_fields=["preferred_date", "preferred_time_slot", "submission_status", "updated_at"])

    ConfirmationHistory.objects.create(
        confirmation=confirmation,
        action=ConfirmationHistoryAction.RESCHEDULED,
        previous_date=prev_date,
        previous_time_slot=prev_slot,
        new_date=new_date,
        new_time_slot=new_slot,
        reason=reason,
        changed_by=actor,
    )

    log_audit_event(
        user=actor,
        action="BOOKING_RESCHEDULED",
        module="scheduling",
        object_type="Confirmation",
        object_id=str(confirmation.id),
        old_values={
            "preferred_date": prev_date.isoformat(),
            "preferred_time_slot": prev_slot.display_label,
        },
        new_values={
            "preferred_date": new_date.isoformat(),
            "preferred_time_slot": new_slot.display_label,
            "reason": reason,
        },
    )
    on_booking_changed(confirmation=confirmation, action="rescheduled", reason=reason)
    return confirmation


@transaction.atomic
def cancel_booking(*, actor: User, confirmation: Confirmation, reason: str = "") -> Confirmation:
    if confirmation.submission_status == ConfirmationStatus.CANCELLED:
        raise DomainError(
            message="Booking is already cancelled.",
            code="BOOKING_ALREADY_CANCELLED",
        )

    prev_status = confirmation.submission_status
    confirmation.submission_status = ConfirmationStatus.CANCELLED
    confirmation.save(update_fields=["submission_status", "updated_at"])

    ConfirmationHistory.objects.create(
        confirmation=confirmation,
        action=ConfirmationHistoryAction.CANCELLED,
        previous_date=confirmation.preferred_date,
        previous_time_slot=confirmation.preferred_time_slot,
        reason=reason,
        changed_by=actor,
    )

    log_audit_event(
        user=actor,
        action="BOOKING_CANCELLED",
        module="scheduling",
        object_type="Confirmation",
        object_id=str(confirmation.id),
        old_values={"submission_status": prev_status},
        new_values={"submission_status": ConfirmationStatus.CANCELLED, "reason": reason},
    )
    on_booking_changed(confirmation=confirmation, action="cancelled", reason=reason)
    return confirmation


@transaction.atomic
def update_booking_experience_status(
    *,
    actor: User,
    confirmation: Confirmation,
    action: str,
    remarks: str,
) -> Confirmation:
    """Update booking experience status (Completed / On Hold / Postponed) with action-based remark."""
    prev_status = confirmation.submission_status
    prev_remarks = confirmation.remarks

    confirmation.submission_status = action
    confirmation.remarks = remarks
    confirmation.save(update_fields=["submission_status", "remarks", "updated_at"])

    ConfirmationHistory.objects.create(
        confirmation=confirmation,
        action=action,
        previous_date=confirmation.preferred_date,
        previous_time_slot=confirmation.preferred_time_slot,
        new_date=confirmation.preferred_date,
        new_time_slot=confirmation.preferred_time_slot,
        reason=remarks,
        changed_by=actor,
    )

    log_audit_event(
        user=actor,
        action="BOOKING_STATUS_UPDATED",
        module="scheduling",
        object_type="Confirmation",
        object_id=str(confirmation.id),
        old_values={"submission_status": prev_status, "remarks": prev_remarks},
        new_values={"submission_status": action, "remarks": remarks},
    )
    on_booking_changed(confirmation=confirmation, action=action, reason=remarks)
    return confirmation
