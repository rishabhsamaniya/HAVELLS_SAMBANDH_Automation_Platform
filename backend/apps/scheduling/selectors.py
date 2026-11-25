"""Reusable availability & scheduling read queries."""
import calendar
from datetime import date, datetime
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db.models import Count, Q

from apps.confirmations.models import Confirmation, ConfirmationStatus
from apps.scheduling.models import BlockedSlot, Holiday, OperatingHoursConfig, TimeSlot


def get_authoritative_today(tz_name: str | None = None) -> date:
    """Return authoritative current date in the campaign's configured timezone."""
    tz = ZoneInfo(tz_name or getattr(settings, "TIME_ZONE", "Asia/Kolkata"))
    return datetime.now(tz).date()


def get_allow_same_day_booking() -> bool:
    config = OperatingHoursConfig.objects.filter(is_active=True).order_by("-created_at").first()
    if config is not None:
        return config.allow_same_day_booking
    return getattr(settings, "ALLOW_SAME_DAY_BOOKING", False)


def _ensure_default_slots_exist() -> None:
    """Auto-seed 24-hour default time slots if the table is completely empty."""
    if not TimeSlot.objects.exists():
        from apps.scheduling.services import generate_time_slots_from_config

        generate_time_slots_from_config()


def get_active_time_slots() -> list[dict]:
    """Return all currently active time slots (for initial public form display)."""
    _ensure_default_slots_exist()
    slots = TimeSlot.objects.filter(is_active=True).order_by("start_time")
    return [
        {
            "id": str(slot.id),
            "label": slot.display_label,
            "start_time": slot.start_time.strftime("%H:%M"),
            "end_time": slot.end_time.strftime("%H:%M"),
            "remaining_capacity": slot.max_capacity,
        }
        for slot in slots
    ]


def get_available_slots_for_date(target_date: date) -> list[dict]:
    """
    Return active, unblocked time slots that still have remaining capacity on target_date.
    Unavailable / full / blocked slots are NOT returned as selectable.
    """
    _ensure_default_slots_exist()
    if Holiday.objects.filter(date=target_date, is_active=True).exists():
        return []

    blocked_slot_ids = set(
        BlockedSlot.objects.filter(date=target_date, is_active=True).values_list(
            "time_slot_id", flat=True
        )
    )

    booked_counts = dict(
        Confirmation.objects.filter(
            preferred_date=target_date,
            submission_status=ConfirmationStatus.CONFIRMED,
        )
        .values("preferred_time_slot_id")
        .annotate(booked=Count("id"))
        .values_list("preferred_time_slot_id", "booked")
    )

    slots = TimeSlot.objects.filter(is_active=True).order_by("start_time")
    available = []
    for slot in slots:
        if slot.id in blocked_slot_ids:
            continue
        booked = booked_counts.get(slot.id, 0)
        remaining = slot.max_capacity - booked
        if remaining > 0:
            available.append(
                {
                    "id": str(slot.id),
                    "label": slot.display_label,
                    "start_time": slot.start_time.strftime("%H:%M"),
                    "end_time": slot.end_time.strftime("%H:%M"),
                    "remaining_capacity": remaining,
                }
            )
    return available


def get_eligible_dates_for_allowed_month(
    *,
    allowed_month: str,
    tz_name: str = "Asia/Kolkata",
    today_override: date | None = None,
) -> list[str]:
    """
    Return ISO date strings (YYYY-MM-DD) strictly within allowed_month that are:
    1. Strictly future relative to authoritative today (or >= today if allow_same_day_booking=True)
    2. Not an active Holiday
    3. Have at least 1 available (active, unblocked, under-capacity) TimeSlot
    """
    year_str, month_str = allowed_month.split("-")
    year, month = int(year_str), int(month_str)
    _, last_day = calendar.monthrange(year, month)

    today = today_override or get_authoritative_today(tz_name)
    allow_same_day = get_allow_same_day_booking()

    # If the allowed month is already completely in the past or future relative to allowed window
    month_end = date(year, month, last_day)
    min_allowed_date = today if allow_same_day else date.fromordinal(today.toordinal() + 1)
    if min_allowed_date > month_end:
        return []

    start_date = max(date(year, month, 1), min_allowed_date)

    holidays = set(
        Holiday.objects.filter(
            date__gte=start_date,
            date__lte=month_end,
            is_active=True,
        ).values_list("date", flat=True)
    )

    _ensure_default_slots_exist()
    active_slots = list(TimeSlot.objects.filter(is_active=True).order_by("start_time"))
    if not active_slots:
        return []

    blocked_pairs = set(
        BlockedSlot.objects.filter(
            date__gte=start_date,
            date__lte=month_end,
            is_active=True,
        ).values_list("date", "time_slot_id")
    )

    booking_counts = {
        (row["preferred_date"], row["preferred_time_slot_id"]): row["booked"]
        for row in Confirmation.objects.filter(
            preferred_date__gte=start_date,
            preferred_date__lte=month_end,
            submission_status=ConfirmationStatus.CONFIRMED,
        )
        .values("preferred_date", "preferred_time_slot_id")
        .annotate(booked=Count("id"))
    }

    eligible: list[str] = []
    current_ord = start_date.toordinal()
    end_ord = month_end.toordinal()

    while current_ord <= end_ord:
        candidate = date.fromordinal(current_ord)
        if candidate not in holidays:
            for slot in active_slots:
                if (candidate, slot.id) in blocked_pairs:
                    continue
                if booking_counts.get((candidate, slot.id), 0) < slot.max_capacity:
                    eligible.append(candidate.isoformat())
                    break
        current_ord += 1

    return eligible
