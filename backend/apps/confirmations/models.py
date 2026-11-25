"""ConfirmationLink, Confirmation, and ConfirmationHistory models."""
import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from apps.campaigns.models import Campaign
from apps.dealers.models import Dealer
from apps.scheduling.models import TimeSlot
from common.models.base import UUIDTimeStampedModel


class ConfirmationLinkStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    SHARED = "shared", "Shared"
    USED = "used", "Used"
    EXPIRED = "expired", "Expired"
    DEACTIVATED = "deactivated", "Deactivated"


class ConfirmationLink(UUIDTimeStampedModel):
    """Personalized, hashed token link allowing a dealer to confirm date & time."""

    dealer = models.ForeignKey(
        Dealer,
        on_delete=models.PROTECT,
        related_name="confirmation_links",
    )
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    encrypted_token = models.TextField(blank=True, default="")
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.PROTECT,
        related_name="confirmation_links",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_confirmation_links",
    )
    assigned_rm = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="rm_confirmation_links",
    )
    shared_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(db_index=True)
    allowed_month = models.CharField(max_length=7, db_index=True)  # Format: YYYY-MM
    status = models.CharField(
        max_length=20,
        choices=ConfirmationLinkStatus.choices,
        default=ConfirmationLinkStatus.ACTIVE,
        db_index=True,
    )
    max_submissions = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    submission_count = models.PositiveIntegerField(default=0)
    is_regenerated = models.BooleanField(default=False, db_index=True)
    regenerated_from = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="regenerated_links",
    )
    regeneration_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "confirmations_confirmationlink"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(max_submissions__gte=1),
                name="chk_link_max_submissions_gte_1",
            ),
            models.CheckConstraint(
                condition=Q(submission_count__lte=F("max_submissions")),
                name="chk_link_sub_count_lte_max",
            ),
        ]
        indexes = [
            models.Index(fields=["dealer", "campaign", "status"], name="idx_link_dealer_camp_status"),
            models.Index(fields=["assigned_rm", "status"], name="idx_link_rm_status"),
            models.Index(fields=["allowed_month", "status"], name="idx_link_month_status"),
        ]

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    def __str__(self) -> str:
        return f"Link({self.dealer.dealer_code} | {self.allowed_month} | {self.status})"


class ConfirmationStatus(models.TextChoices):
    CONFIRMED = "confirmed", "Confirmed"
    RESCHEDULED = "rescheduled", "Rescheduled"
    EXPERIENCE_COMPLETED = "experience_completed", "Experience Completed"
    EXPERIENCE_ON_HOLD = "experience_on_hold", "Experience on Hold"
    EXPERIENCE_POSTPONED = "experience_postponed", "Experience Postponed"
    CANCELLED = "cancelled", "Cancelled"


class Confirmation(UUIDTimeStampedModel):
    """Submitted dealer date & time confirmation record."""

    dealer = models.ForeignKey(
        Dealer,
        on_delete=models.PROTECT,
        related_name="confirmations",
    )
    confirmation_link = models.ForeignKey(
        ConfirmationLink,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="confirmations",
    )
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.PROTECT,
        related_name="confirmations",
    )
    preferred_date = models.DateField(db_index=True)
    preferred_time_slot = models.ForeignKey(
        TimeSlot,
        on_delete=models.PROTECT,
        related_name="confirmations",
    )
    submission_status = models.CharField(
        max_length=30,
        choices=ConfirmationStatus.choices,
        default=ConfirmationStatus.CONFIRMED,
        db_index=True,
    )
    remarks = models.CharField(max_length=255, blank=True, default="")
    submitted_at = models.DateTimeField(default=timezone.now, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="manual_confirmations",
    )

    class Meta:
        db_table = "confirmations_confirmation"
        ordering = ["-submitted_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["confirmation_link"],
                condition=Q(
                    confirmation_link__isnull=False,
                    submission_status=ConfirmationStatus.CONFIRMED,
                ),
                name="uq_active_confirmation_per_link",
            ),
        ]
        indexes = [
            models.Index(
                fields=["preferred_date", "preferred_time_slot", "submission_status"],
                name="idx_conf_date_slot_status",
            ),
            models.Index(fields=["dealer", "submitted_at"], name="idx_conf_dealer_submitted"),
            models.Index(fields=["campaign", "submission_status"], name="idx_conf_campaign_status"),
        ]

    def __str__(self) -> str:
        return f"{self.dealer.dealer_code} @ {self.preferred_date} ({self.preferred_time_slot.display_label})"


class ConfirmationHistoryAction(models.TextChoices):
    CREATED = "created", "Created"
    RESCHEDULED = "rescheduled", "Rescheduled"
    EXPERIENCE_COMPLETED = "experience_completed", "Experience Completed"
    EXPERIENCE_ON_HOLD = "experience_on_hold", "Experience on Hold"
    EXPERIENCE_POSTPONED = "experience_postponed", "Experience Postponed"
    CANCELLED = "cancelled", "Cancelled"


class ConfirmationHistory(models.Model):
    """Immutable change history for booking reschedules, status updates, and cancellations."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    confirmation = models.ForeignKey(
        Confirmation,
        on_delete=models.CASCADE,
        related_name="history",
    )
    action = models.CharField(max_length=30, choices=ConfirmationHistoryAction.choices)
    previous_date = models.DateField(null=True, blank=True)
    previous_time_slot = models.ForeignKey(
        TimeSlot,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    new_date = models.DateField(null=True, blank=True)
    new_time_slot = models.ForeignKey(
        TimeSlot,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    reason = models.TextField(blank=True, default="")
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="confirmation_changes",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "confirmations_confirmationhistory"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.confirmation_id} | {self.action}"
