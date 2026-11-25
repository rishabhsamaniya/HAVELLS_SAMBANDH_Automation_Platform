"""Business logic services for Confirmation Link Generation, Bulk Generation, Copy-Share & Regeneration."""
import calendar
from datetime import datetime
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import status

from apps.accounts.models import User
from apps.audit_logs.services import log_audit_event
from apps.campaigns.models import Campaign, CampaignStatus
from apps.confirmations.models import ConfirmationLink, ConfirmationLinkStatus
from apps.dealers.models import Dealer, DealerStatus
from apps.dealers.selectors import get_scoped_dealers_queryset
from apps.notifications.services import on_link_generated, on_link_shared
from apps.permissions.services import PermissionService
from apps.scheduling.selectors import get_authoritative_today
from common.exceptions.domain import DomainError, ForbiddenError
from services.tokens import decrypt_token, encrypt_token, generate_secure_token, hash_token


def build_shareable_url(raw_token: str) -> str:
    base_url = getattr(settings, "FRONTEND_BASE_URL", "http://localhost:5173").rstrip("/")
    return f"{base_url}/confirm/{raw_token}"


def build_share_message(*, campaign_name: str, shareable_url: str) -> str:
    return (
        "Dear Partner,\n\n"
        "Greetings from Havells Sambandh Surprises.\n\n"
        "A heartfelt thank you from Havells for your continued trust, partnership, and contributions.\n\n"
        "To celebrate this moment and make it a memorable experience, please confirm your preferred date and time using the link below.\n\n"
        f"Link: {shareable_url}\n\n"
        "Regards,\n"
        "Havells Sambandh Surprises"
    )


def _compute_allowed_month_and_expiry(campaign: Campaign, expires_at: datetime | None = None) -> tuple[str, datetime]:
    tz_name = campaign.timezone or getattr(settings, "TIME_ZONE", "Asia/Kolkata")
    tz = ZoneInfo(tz_name)
    today = get_authoritative_today(tz_name)
    allowed_month = f"{today.year:04d}-{today.month:02d}"
    _, last_day = calendar.monthrange(today.year, today.month)
    month_end_dt = datetime(today.year, today.month, last_day, 23, 59, 59, tzinfo=tz)

    if expires_at is None:
        return allowed_month, month_end_dt

    resolved_expiry = expires_at if timezone.is_aware(expires_at) else expires_at.replace(tzinfo=tz)
    if resolved_expiry <= timezone.now():
        raise DomainError(
            message="Expiry timestamp must be in the future.",
            code="INVALID_EXPIRY",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    if resolved_expiry > month_end_dt:
        raise DomainError(
            message=f"Link expiry cannot exceed the end of the allowed month ({allowed_month}).",
            code="EXPIRY_EXCEEDS_ALLOWED_MONTH",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return allowed_month, resolved_expiry


@transaction.atomic
def generate_confirmation_link(
    *,
    actor: User,
    dealer: Dealer,
    campaign: Campaign,
    expires_at: datetime | None = None,
    max_submissions: int = 1,
    is_regenerated: bool = False,
    regenerated_from: ConfirmationLink | None = None,
) -> dict:
    """
    Generate a cryptographically secure, single-dealer confirmation link.
    Stores SHA-256 hash + authenticated encrypted token (never plain text).
    """
    if not PermissionService.can_access_all_dealers(actor) and dealer.assigned_rm_id != actor.id:
        raise ForbiddenError(
            message="You can only generate confirmation links for your assigned dealers.",
            code="RM_DEALER_SCOPE_VIOLATION",
        )

    if dealer.status != DealerStatus.ACTIVE:
        raise DomainError(
            message="Cannot generate a confirmation link for an inactive dealer.",
            code="DEALER_INACTIVE",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if campaign.status != CampaignStatus.ACTIVE:
        raise DomainError(
            message="Cannot generate a confirmation link for an inactive campaign.",
            code="CAMPAIGN_INACTIVE",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    allowed_month, resolved_expiry = _compute_allowed_month_and_expiry(campaign, expires_at)

    if getattr(settings, "AUTO_REVOKE_PRIOR_LINK", True):
        ConfirmationLink.objects.filter(
            dealer=dealer,
            campaign=campaign,
            status__in=[ConfirmationLinkStatus.ACTIVE, ConfirmationLinkStatus.SHARED],
        ).update(status=ConfirmationLinkStatus.DEACTIVATED, updated_at=timezone.now())

    raw_token = generate_secure_token(32)
    next_regen_count = (regenerated_from.regeneration_count + 1) if regenerated_from else (1 if is_regenerated else 0)

    link = ConfirmationLink.objects.create(
        dealer=dealer,
        token_hash=hash_token(raw_token),
        encrypted_token=encrypt_token(raw_token),
        campaign=campaign,
        created_by=actor,
        assigned_rm=dealer.assigned_rm,
        expires_at=resolved_expiry,
        allowed_month=allowed_month,
        status=ConfirmationLinkStatus.ACTIVE,
        max_submissions=max_submissions,
        is_regenerated=is_regenerated,
        regenerated_from=regenerated_from,
        regeneration_count=next_regen_count,
    )

    shareable_url = build_shareable_url(raw_token)
    share_message = build_share_message(
        campaign_name=campaign.campaign_name,
        shareable_url=shareable_url,
    )

    log_audit_event(
        user=actor,
        action="CONFIRMATION_LINK_REGENERATED" if is_regenerated else "CONFIRMATION_LINK_GENERATED",
        module="confirmations",
        object_type="ConfirmationLink",
        object_id=str(link.id),
        new_values={
            "dealer_code": dealer.dealer_code,
            "campaign_code": campaign.campaign_code,
            "allowed_month": allowed_month,
            "expires_at": resolved_expiry.isoformat(),
            "is_regenerated": is_regenerated,
            "regeneration_count": next_regen_count,
        },
    )
    on_link_generated(link=link, share_message=share_message)

    return {
        "link": link,
        "shareable_url": shareable_url,
        "share_message": share_message,
    }


@transaction.atomic
def bulk_generate_confirmation_links(
    *,
    actor: User,
    campaign: Campaign,
    dealer_ids: list | None = None,
    select_all_active: bool = False,
    expires_at: datetime | None = None,
) -> dict:
    """
    Generate confirmation links in bulk for authorized dealers under a campaign.
    Automatically skips dealers who already have an active, shared, or used link
    for this campaign so a dealer never receives accidental duplicate links.
    """
    if campaign.status != CampaignStatus.ACTIVE:
        raise DomainError(
            message="Cannot generate links for an inactive campaign.",
            code="CAMPAIGN_INACTIVE",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    scoped_dealers = get_scoped_dealers_queryset(actor).filter(status=DealerStatus.ACTIVE)
    if not select_all_active:
        if not dealer_ids:
            raise DomainError(
                message="Select at least one dealer or enable select_all_active.",
                code="DEALERS_REQUIRED",
            )
        dealers = list(scoped_dealers.filter(id__in=dealer_ids))
    else:
        dealers = list(scoped_dealers)

    if not dealers:
        raise DomainError(
            message="No eligible active dealers found in your scope.",
            code="NO_ELIGIBLE_DEALERS",
        )

    existing_dealer_ids = set(
        ConfirmationLink.objects.filter(
            campaign=campaign,
            dealer_id__in=[d.id for d in dealers],
            status__in=[
                ConfirmationLinkStatus.ACTIVE,
                ConfirmationLinkStatus.SHARED,
                ConfirmationLinkStatus.USED,
            ],
        ).values_list("dealer_id", flat=True)
    )

    created_links = []
    skipped = []

    for dealer in dealers:
        if dealer.id in existing_dealer_ids:
            skipped.append(
                {
                    "dealer_id": str(dealer.id),
                    "dealer_code": dealer.dealer_code,
                    "reason": "Link already exists for this campaign. Use Regenerate to issue a new link.",
                }
            )
            continue

        result = generate_confirmation_link(
            actor=actor,
            dealer=dealer,
            campaign=campaign,
            expires_at=expires_at,
        )
        created_links.append(result)

    log_audit_event(
        user=actor,
        action="CONFIRMATION_LINKS_BULK_GENERATED",
        module="confirmations",
        object_type="Campaign",
        object_id=str(campaign.id),
        new_values={
            "campaign_code": campaign.campaign_code,
            "created_count": len(created_links),
            "skipped_count": len(skipped),
        },
    )

    return {
        "created_count": len(created_links),
        "skipped_count": len(skipped),
        "created_links": created_links,
        "skipped": skipped,
    }


@transaction.atomic
def get_copyable_link_and_mark_shared(*, actor: User, link: ConfirmationLink) -> dict:
    """
    Decrypt an active/shared link anytime for RM copying and automatically
    mark the link as shared so the Dashboard 'Links Shared' KPI increments.
    """
    if link.status in (ConfirmationLinkStatus.DEACTIVATED, ConfirmationLinkStatus.EXPIRED) or link.is_expired:
        raise DomainError(
            message="This link is expired or deactivated. Use Regenerate to create a fresh link.",
            code="LINK_NOT_COPYABLE",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if link.status == ConfirmationLinkStatus.USED:
        raise DomainError(
            message="This dealer has already submitted their confirmation using this link.",
            code="LINK_ALREADY_USED",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if not link.encrypted_token:
        raise DomainError(
            message="This legacy link cannot be copied again. Please click Regenerate to issue a copyable link.",
            code="LINK_REQUIRES_REGENERATE",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    raw_token = decrypt_token(link.encrypted_token)
    shareable_url = build_shareable_url(raw_token)
    share_message = build_share_message(
        campaign_name=link.campaign.campaign_name,
        shareable_url=shareable_url,
    )

    # Automatically mark as shared if not yet shared (increments Dashboard 'Links Shared')
    if link.shared_at is None or link.status == ConfirmationLinkStatus.ACTIVE:
        old_status = link.status
        if link.shared_at is None:
            link.shared_at = timezone.now()
        if link.status == ConfirmationLinkStatus.ACTIVE:
            link.status = ConfirmationLinkStatus.SHARED
        link.save(update_fields=["shared_at", "status", "updated_at"])
        log_audit_event(
            user=actor,
            action="CONFIRMATION_LINK_SHARED",
            module="confirmations",
            object_type="ConfirmationLink",
            object_id=str(link.id),
            old_values={"status": old_status},
            new_values={"status": link.status, "shared_at": link.shared_at.isoformat()},
        )
        on_link_shared(link=link)

    return {
        "link": link,
        "shareable_url": shareable_url,
        "share_message": share_message,
    }


@transaction.atomic
def regenerate_confirmation_link(
    *,
    actor: User,
    existing_link: ConfirmationLink,
    expires_at: datetime | None = None,
) -> dict:
    """
    Rotate an existing confirmation link IN PLACE (no duplicate row created):
    - Replaces token_hash & encrypted_token so the old URL is immediately invalidated.
    - Keeps a single ConfirmationLink record for the dealer + campaign.
    - Increments regeneration_count so Dashboard & RM-wise regenerated counts increase accurately.
    """
    link = (
        ConfirmationLink.objects.select_for_update()
        .select_related("dealer", "campaign", "assigned_rm")
        .get(pk=existing_link.pk)
    )

    if not PermissionService.can_access_all_dealers(actor) and link.assigned_rm_id != actor.id:
        raise ForbiddenError(
            message="You can only regenerate confirmation links for your assigned dealers.",
            code="RM_DEALER_SCOPE_VIOLATION",
        )

    if link.status == ConfirmationLinkStatus.USED:
        raise DomainError(
            message="Cannot regenerate a link that has already been submitted. Use Scheduling → Reschedule instead.",
            code="LINK_ALREADY_USED",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if link.dealer.status != DealerStatus.ACTIVE:
        raise DomainError(
            message="Cannot regenerate a confirmation link for an inactive dealer.",
            code="DEALER_INACTIVE",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if link.campaign.status != CampaignStatus.ACTIVE:
        raise DomainError(
            message="Cannot regenerate a confirmation link for an inactive campaign.",
            code="CAMPAIGN_INACTIVE",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    allowed_month, resolved_expiry = _compute_allowed_month_and_expiry(link.campaign, expires_at)
    raw_token = generate_secure_token(32)
    old_count = link.regeneration_count
    old_status = link.status

    link.token_hash = hash_token(raw_token)
    link.encrypted_token = encrypt_token(raw_token)
    link.allowed_month = allowed_month
    link.expires_at = resolved_expiry
    link.status = ConfirmationLinkStatus.ACTIVE
    link.shared_at = None
    link.submission_count = 0
    link.is_regenerated = True
    link.regeneration_count = old_count + 1
    link.save(
        update_fields=[
            "token_hash",
            "encrypted_token",
            "allowed_month",
            "expires_at",
            "status",
            "shared_at",
            "submission_count",
            "is_regenerated",
            "regeneration_count",
            "updated_at",
        ]
    )

    shareable_url = build_shareable_url(raw_token)
    share_message = build_share_message(
        campaign_name=link.campaign.campaign_name,
        shareable_url=shareable_url,
    )

    log_audit_event(
        user=actor,
        action="CONFIRMATION_LINK_REGENERATED",
        module="confirmations",
        object_type="ConfirmationLink",
        object_id=str(link.id),
        old_values={"status": old_status, "regeneration_count": old_count},
        new_values={
            "dealer_code": link.dealer.dealer_code,
            "campaign_code": link.campaign.campaign_code,
            "status": link.status,
            "allowed_month": allowed_month,
            "regeneration_count": link.regeneration_count,
        },
    )
    on_link_generated(link=link, share_message=share_message)

    return {
        "link": link,
        "shareable_url": shareable_url,
        "share_message": share_message,
    }


@transaction.atomic
def mark_confirmation_link_shared(*, actor: User, link: ConfirmationLink) -> ConfirmationLink:
    if link.status in (ConfirmationLinkStatus.DEACTIVATED, ConfirmationLinkStatus.EXPIRED):
        raise DomainError(
            message="Cannot mark a deactivated or expired link as shared.",
            code="INVALID_LINK_STATE",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    old_status = link.status
    link.shared_at = timezone.now()
    if link.status == ConfirmationLinkStatus.ACTIVE:
        link.status = ConfirmationLinkStatus.SHARED
    link.save(update_fields=["shared_at", "status", "updated_at"])

    log_audit_event(
        user=actor,
        action="CONFIRMATION_LINK_SHARED",
        module="confirmations",
        object_type="ConfirmationLink",
        object_id=str(link.id),
        old_values={"status": old_status},
        new_values={"status": link.status, "shared_at": link.shared_at.isoformat()},
    )
    on_link_shared(link=link)
    return link


@transaction.atomic
def deactivate_confirmation_link(*, actor: User, link: ConfirmationLink) -> ConfirmationLink:
    old_status = link.status
    link.status = ConfirmationLinkStatus.DEACTIVATED
    link.save(update_fields=["status", "updated_at"])

    log_audit_event(
        user=actor,
        action="CONFIRMATION_LINK_DEACTIVATED",
        module="confirmations",
        object_type="ConfirmationLink",
        object_id=str(link.id),
        old_values={"status": old_status},
        new_values={"status": link.status},
    )
    return link
