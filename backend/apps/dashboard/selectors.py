"""Real-time, RBAC-scoped database aggregation selectors for Admin Dashboard."""
from datetime import date

from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce, TruncDate, TruncMonth
from django.utils import timezone

from apps.accounts.models import User
from apps.confirmations.models import ConfirmationLinkStatus, ConfirmationStatus
from apps.confirmations.selectors import (
    get_scoped_confirmation_links_queryset,
    get_scoped_confirmations_queryset,
)
from apps.dealers.selectors import get_scoped_dealers_queryset
from apps.scheduling.models import TimeSlot
from apps.scheduling.selectors import get_authoritative_today


def _apply_filters(links_qs, confs_qs, *, campaign_id=None, start_date: date | None = None, end_date: date | None = None):
    if campaign_id:
        links_qs = links_qs.filter(campaign_id=campaign_id)
        confs_qs = confs_qs.filter(campaign_id=campaign_id)
    if start_date:
        links_qs = links_qs.filter(created_at__date__gte=start_date)
        confs_qs = confs_qs.filter(submitted_at__date__gte=start_date)
    if end_date:
        links_qs = links_qs.filter(created_at__date__lte=end_date)
        confs_qs = confs_qs.filter(submitted_at__date__lte=end_date)
    return links_qs, confs_qs


def get_dashboard_overview(
    *,
    user: User,
    campaign_id=None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict:
    dealers_qs = get_scoped_dealers_queryset(user)
    links_qs = get_scoped_confirmation_links_queryset(user)
    confs_qs = get_scoped_confirmations_queryset(user)

    links_qs, confs_qs = _apply_filters(
        links_qs, confs_qs, campaign_id=campaign_id, start_date=start_date, end_date=end_date
    )

    today = get_authoritative_today()
    now = timezone.now()

    total_dealers = dealers_qs.count()
    total_links = links_qs.count()
    links_shared = links_qs.filter(shared_at__isnull=False).count()
    regenerated_links = links_qs.aggregate(total=Coalesce(Sum("regeneration_count"), 0))["total"]
    expired_links = links_qs.filter(
        Q(status=ConfirmationLinkStatus.EXPIRED)
        | Q(
            status__in=[ConfirmationLinkStatus.ACTIVE, ConfirmationLinkStatus.SHARED],
            expires_at__lt=now,
        )
    ).count()
    pending_confirmations = links_qs.filter(
        status__in=[ConfirmationLinkStatus.ACTIVE, ConfirmationLinkStatus.SHARED],
        expires_at__gte=now,
    ).count()

    confirmed_qs = confs_qs.filter(submission_status=ConfirmationStatus.CONFIRMED)
    confirmations_received = confirmed_qs.count()
    todays_confirmations = confirmed_qs.filter(submitted_at__date=today).count()
    upcoming_bookings = confirmed_qs.filter(preferred_date__gte=today).count()

    return {
        "total_dealers": total_dealers,
        "total_confirmation_links": total_links,
        "links_shared": links_shared,
        "regenerated_links": regenerated_links,
        "confirmations_received": confirmations_received,
        "pending_confirmations": pending_confirmations,
        "expired_links": expired_links,
        "todays_confirmations": todays_confirmations,
        "upcoming_bookings": upcoming_bookings,
    }


def get_dashboard_analytics(
    *,
    user: User,
    campaign_id=None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict:
    links_qs = get_scoped_confirmation_links_queryset(user)
    confs_qs = get_scoped_confirmations_queryset(user)
    links_qs, confs_qs = _apply_filters(
        links_qs, confs_qs, campaign_id=campaign_id, start_date=start_date, end_date=end_date
    )

    confirmed_qs = confs_qs.filter(submission_status=ConfirmationStatus.CONFIRMED)
    now = timezone.now()

    # 1. Daily confirmations
    daily_confirmations = [
        {"date": row["day"].isoformat(), "count": row["count"]}
        for row in confirmed_qs.annotate(day=TruncDate("submitted_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
        if row["day"] is not None
    ]

    # 2. Monthly confirmations
    monthly_confirmations = [
        {"month": row["month"].strftime("%Y-%m"), "count": row["count"]}
        for row in confirmed_qs.annotate(month=TruncMonth("submitted_at"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
        if row["month"] is not None
    ]

    # 3. RM-wise performance
    rm_link_stats = {
        row["assigned_rm_id"]: row
        for row in links_qs.values("assigned_rm_id", "assigned_rm__full_name").annotate(
            total_links=Count("id"),
            shared_links=Count("id", filter=Q(shared_at__isnull=False)),
            regenerated_links=Coalesce(Sum("regeneration_count"), 0),
            pending_links=Count(
                "id",
                filter=Q(
                    status__in=[ConfirmationLinkStatus.ACTIVE, ConfirmationLinkStatus.SHARED],
                    expires_at__gte=now,
                ),
            ),
            expired_links=Count(
                "id",
                filter=Q(status=ConfirmationLinkStatus.EXPIRED)
                | Q(
                    status__in=[ConfirmationLinkStatus.ACTIVE, ConfirmationLinkStatus.SHARED],
                    expires_at__lt=now,
                ),
            ),
        )
    }
    rm_conf_counts = dict(
        confirmed_qs.values("dealer__assigned_rm_id")
        .annotate(confirmed=Count("id"))
        .values_list("dealer__assigned_rm_id", "confirmed")
    )
    rm_performance = []
    for rm_id, stats in rm_link_stats.items():
        confirmed = rm_conf_counts.get(rm_id, 0)
        total = stats["total_links"]
        rm_performance.append(
            {
                "rm_id": str(rm_id),
                "rm_name": stats["assigned_rm__full_name"],
                "total_links": total,
                "shared_links": stats["shared_links"],
                "regenerated_links": stats["regenerated_links"],
                "confirmed": confirmed,
                "pending": stats["pending_links"],
                "expired": stats["expired_links"],
                "conversion_rate": round((confirmed / total) * 100, 1) if total else 0.0,
            }
        )

    # 4. Campaign-wise performance
    camp_link_stats = {
        row["campaign_id"]: row
        for row in links_qs.values("campaign_id", "campaign__campaign_name").annotate(
            total_links=Count("id"),
            pending_links=Count(
                "id",
                filter=Q(
                    status__in=[ConfirmationLinkStatus.ACTIVE, ConfirmationLinkStatus.SHARED],
                    expires_at__gte=now,
                ),
            ),
        )
    }
    camp_conf_counts = dict(
        confirmed_qs.values("campaign_id")
        .annotate(confirmed=Count("id"))
        .values_list("campaign_id", "confirmed")
    )
    campaign_performance = []
    for cid, stats in camp_link_stats.items():
        confirmed = camp_conf_counts.get(cid, 0)
        total = stats["total_links"]
        campaign_performance.append(
            {
                "campaign_id": str(cid),
                "campaign_name": stats["campaign__campaign_name"],
                "total_links": total,
                "confirmed": confirmed,
                "pending": stats["pending_links"],
                "conversion_rate": round((confirmed / total) * 100, 1) if total else 0.0,
            }
        )

    # 5. Date-wise booking distribution
    date_wise_bookings = [
        {"date": row["preferred_date"].isoformat(), "count": row["count"]}
        for row in confirmed_qs.values("preferred_date")
        .annotate(count=Count("id"))
        .order_by("preferred_date")
    ]

    # 6. Time-slot utilization
    slot_counts = dict(
        confirmed_qs.values("preferred_time_slot_id")
        .annotate(booked=Count("id"))
        .values_list("preferred_time_slot_id", "booked")
    )
    time_slot_utilization = [
        {
            "slot_id": str(slot.id),
            "label": slot.display_label,
            "booked": slot_counts.get(slot.id, 0),
            "max_capacity": slot.max_capacity,
        }
        for slot in TimeSlot.objects.filter(is_active=True).order_by("start_time")
    ]

    # 7. Pending vs Confirmed comparison
    pending_count = links_qs.filter(
        status__in=[ConfirmationLinkStatus.ACTIVE, ConfirmationLinkStatus.SHARED],
        expires_at__gte=now,
    ).count()
    confirmed_count = confirmed_qs.count()
    expired_count = links_qs.filter(
        Q(status=ConfirmationLinkStatus.EXPIRED)
        | Q(
            status__in=[ConfirmationLinkStatus.ACTIVE, ConfirmationLinkStatus.SHARED],
            expires_at__lt=now,
        )
    ).count()

    return {
        "daily_confirmations": daily_confirmations,
        "monthly_confirmations": monthly_confirmations,
        "rm_performance": rm_performance,
        "campaign_performance": campaign_performance,
        "date_wise_bookings": date_wise_bookings,
        "time_slot_utilization": time_slot_utilization,
        "pending_vs_confirmed": {
            "confirmed": confirmed_count,
            "pending": pending_count,
            "expired": expired_count,
        },
    }
