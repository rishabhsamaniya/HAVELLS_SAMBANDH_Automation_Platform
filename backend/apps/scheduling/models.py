"""Scheduling engine models: OperatingHoursConfig, TimeSlot, Holiday, BlockedSlot."""
from datetime import time

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q

from common.models.base import UUIDTimeStampedModel


class OperatingHoursConfig(UUIDTimeStampedModel):
    """Admin-configurable operating hours and global booking defaults."""

    opening_time = models.TimeField(default=time(10, 0))
    closing_time = models.TimeField(default=time(18, 0))
    slot_duration = models.PositiveIntegerField(default=60, validators=[MinValueValidator(15)])
    default_capacity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    allow_same_day_booking = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "scheduling_operatinghoursconfig"
        constraints = [
            models.CheckConstraint(
                condition=Q(closing_time__gt=F("opening_time")),
                name="chk_operating_hours_close_gt_open",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.opening_time:%H:%M} - {self.closing_time:%H:%M} ({self.slot_duration}m)"


class TimeSlot(UUIDTimeStampedModel):
    """Configurable one-hour (default) booking slot."""

    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_duration = models.PositiveIntegerField(default=60, validators=[MinValueValidator(15)])
    max_capacity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "scheduling_timeslot"
        ordering = ["start_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["start_time", "end_time"],
                name="uq_timeslot_start_end",
            ),
            models.CheckConstraint(
                condition=Q(end_time__gt=F("start_time")),
                name="chk_timeslot_end_gt_start",
            ),
            models.CheckConstraint(
                condition=Q(max_capacity__gte=1),
                name="chk_timeslot_max_capacity_gte_1",
            ),
        ]

    @property
    def display_label(self) -> str:
        """Readable AM/PM label e.g. '10:00 AM – 11:00 AM'."""
        return f"{self.start_time.strftime('%I:%M %p')} – {self.end_time.strftime('%I:%M %p')}"

    def __str__(self) -> str:
        return self.display_label


class Holiday(UUIDTimeStampedModel):
    """Full-day holiday preventing bookings on a specific calendar date."""

    date = models.DateField(unique=True, db_index=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_holidays",
    )

    class Meta:
        db_table = "scheduling_holiday"
        ordering = ["date"]

    def __str__(self) -> str:
        return f"{self.date} - {self.name}"


class BlockedSlot(UUIDTimeStampedModel):
    """Blocks a specific (date, time_slot) combination from accepting bookings."""

    date = models.DateField(db_index=True)
    time_slot = models.ForeignKey(
        TimeSlot,
        on_delete=models.PROTECT,
        related_name="blocked_dates",
    )
    reason = models.CharField(max_length=255, blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_blocked_slots",
    )

    class Meta:
        db_table = "scheduling_blockedslot"
        ordering = ["date", "time_slot__start_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["date", "time_slot"],
                name="uq_blocked_date_slot",
            ),
        ]
        indexes = [
            models.Index(fields=["date", "is_active"], name="idx_blockedslot_date_active"),
        ]

    def __str__(self) -> str:
        return f"{self.date} | {self.time_slot.display_label}"
