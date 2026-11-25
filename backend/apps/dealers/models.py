"""Dealer master model."""
from django.conf import settings
from django.db import models

from common.models.base import UUIDTimeStampedModel
from common.validators.mobile import (
    normalize_dealer_code,
    normalize_indian_mobile,
    validate_indian_mobile,
)


class DealerStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"


class Dealer(UUIDTimeStampedModel):
    """Internal Havells dealer master record (no dealer name on public confirmation form)."""

    dealer_code = models.CharField(max_length=64, unique=True, db_index=True)
    mobile_number = models.CharField(
        max_length=15,
        validators=[validate_indian_mobile],
        db_index=True,
    )
    status = models.CharField(
        max_length=20,
        choices=DealerStatus.choices,
        default=DealerStatus.ACTIVE,
        db_index=True,
    )
    assigned_rm = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="assigned_dealers",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_dealers",
    )

    class Meta:
        db_table = "dealers_dealer"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["assigned_rm", "status"], name="idx_dealer_rm_status"),
            models.Index(fields=["dealer_code", "mobile_number"], name="idx_dealer_code_mobile"),
        ]

    def save(self, *args, **kwargs):
        self.dealer_code = normalize_dealer_code(self.dealer_code)
        self.mobile_number = normalize_indian_mobile(self.mobile_number)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.dealer_code} ({self.mobile_number})"
