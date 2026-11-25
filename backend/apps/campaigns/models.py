"""Campaign model supporting current and future engagement programs."""
from django.conf import settings
from django.db import models
from django.db.models import F, Q

from common.models.base import UUIDTimeStampedModel


class CampaignStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    PAUSED = "paused", "Paused"
    COMPLETED = "completed", "Completed"
    ARCHIVED = "archived", "Archived"


class Campaign(UUIDTimeStampedModel):
    """Dealer engagement campaign container."""

    campaign_name = models.CharField(max_length=200)
    campaign_code = models.CharField(max_length=64, unique=True, db_index=True)
    description = models.TextField(blank=True, default="")
    start_date = models.DateField()
    end_date = models.DateField()
    timezone = models.CharField(max_length=64, default="Asia/Kolkata")
    status = models.CharField(
        max_length=20,
        choices=CampaignStatus.choices,
        default=CampaignStatus.ACTIVE,
        db_index=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_campaigns",
    )

    class Meta:
        db_table = "campaigns_campaign"
        ordering = ["-start_date", "-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(end_date__gte=F("start_date")),
                name="chk_campaign_end_gte_start",
            ),
        ]
        indexes = [
            models.Index(fields=["status", "start_date", "end_date"], name="idx_campaign_status_dates"),
        ]

    def save(self, *args, **kwargs):
        self.campaign_code = self.campaign_code.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.campaign_name} ({self.campaign_code})"
