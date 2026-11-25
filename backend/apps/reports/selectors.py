"""RBAC-scoped report builders for all 8 Havells Sambandh reports."""
from datetime import date

from django.db.models import Count, Q
from django.utils import timezone

from apps.accounts.models import User
from apps.confirmations.models import ConfirmationLinkStatus, ConfirmationStatus
from apps.confirmations.selectors import (
    get_scoped_confirmation_links_queryset,
    get_scoped_confirmations_queryset,
)
from apps.dealers.selectors import get_scoped_dealers_queryset
from apps.scheduling.models import TimeSlot


def _filter_dealers(user: User, filters: dict):
    qs = get_scoped_dealers_queryset(user)
    if filters.get("assigned_rm"):
        qs = qs.filter(assigned_rm_id=filters["assigned_rm"])
    if filters.get("dealer_code"):
        qs = qs.filter(dealer_code__icontains=filters["dealer_code"].strip())
    if filters.get("status"):
        qs = qs.filter(status=filters["status"])
    return qs


def _filter_links(user: User, filters: dict):
    qs = get_scoped_confirmation_links_queryset(user)
    if filters.get("campaign"):
        qs = qs.filter(campaign_id=filters["campaign"])
    if filters.get("assigned_rm"):
        qs = qs.filter(assigned_rm_id=filters["assigned_rm"])
    if filters.get("dealer_code"):
        qs = qs.filter(dealer__dealer_code__icontains=filters["dealer_code"].strip())
    if filters.get("status"):
        qs = qs.filter(status=filters["status"])
    if filters.get("start_date"):
        qs = qs.filter(created_at__date__gte=filters["start_date"])
    if filters.get("end_date"):
        qs = qs.filter(created_at__date__lte=filters["end_date"])
    return qs


def _filter_confirmations(user: User, filters: dict):
    qs = get_scoped_confirmations_queryset(user)
    if filters.get("campaign"):
        qs = qs.filter(campaign_id=filters["campaign"])
    if filters.get("assigned_rm"):
        qs = qs.filter(dealer__assigned_rm_id=filters["assigned_rm"])
    if filters.get("dealer_code"):
        qs = qs.filter(dealer__dealer_code__icontains=filters["dealer_code"].strip())
    if filters.get("status"):
        qs = qs.filter(submission_status=filters["status"])
    if filters.get("start_date"):
        qs = qs.filter(preferred_date__gte=filters["start_date"])
    if filters.get("end_date"):
        qs = qs.filter(preferred_date__lte=filters["end_date"])
    return qs


def build_dealer_master_report(user: User, filters: dict) -> tuple[list[str], list[dict]]:
    headers = ["Dealer Code", "Mobile Number", "Status", "Assigned RM", "RM Mobile", "Created At"]
    rows = [
        {
            "Dealer Code": d.dealer_code,
            "Mobile Number": d.mobile_number,
            "Status": d.status,
            "Assigned RM": d.assigned_rm.full_name,
            "RM Mobile": d.assigned_rm.mobile_number,
            "Created At": d.created_at.strftime("%Y-%m-%d %H:%M"),
        }
        for d in _filter_dealers(user, filters)
    ]
    return headers, rows


def build_confirmation_report(user: User, filters: dict) -> tuple[list[str], list[dict]]:
    headers = [
        "Dealer Code",
        "Mobile Number",
        "Assigned RM",
        "Campaign",
        "Preferred Date",
        "Preferred Time Slot",
        "Status",
        "Submitted At",
    ]
    rows = [
        {
            "Dealer Code": c.dealer.dealer_code,
            "Mobile Number": c.dealer.mobile_number,
            "Assigned RM": c.dealer.assigned_rm.full_name,
            "Campaign": c.campaign.campaign_name,
            "Preferred Date": c.preferred_date.isoformat(),
            "Preferred Time Slot": c.preferred_time_slot.display_label,
            "Status": c.submission_status,
            "Submitted At": c.submitted_at.strftime("%Y-%m-%d %H:%M"),
        }
        for c in _filter_confirmations(user, filters)
    ]
    return headers, rows


def build_pending_dealer_report(user: User, filters: dict) -> tuple[list[str], list[dict]]:
    now = timezone.now()
    qs = _filter_links(user, filters).filter(
        status__in=[ConfirmationLinkStatus.ACTIVE, ConfirmationLinkStatus.SHARED],
        expires_at__gte=now,
    )
    headers = ["Dealer Code", "Mobile Number", "Assigned RM", "Campaign", "Allowed Month", "Link Status", "Expires At"]
    rows = [
        {
            "Dealer Code": lnk.dealer.dealer_code,
            "Mobile Number": lnk.dealer.mobile_number,
            "Assigned RM": lnk.assigned_rm.full_name,
            "Campaign": lnk.campaign.campaign_name,
            "Allowed Month": lnk.allowed_month,
            "Link Status": lnk.status,
            "Expires At": lnk.expires_at.strftime("%Y-%m-%d %H:%M"),
        }
        for lnk in qs
    ]
    return headers, rows


def build_rm_wise_report(user: User, filters: dict) -> tuple[list[str], list[dict]]:
    now = timezone.now()
    links_qs = _filter_links(user, filters)
    confs_qs = _filter_confirmations(user, filters).filter(submission_status=ConfirmationStatus.CONFIRMED)

    link_stats = {
        row["assigned_rm_id"]: row
        for row in links_qs.values("assigned_rm_id", "assigned_rm__full_name", "assigned_rm__mobile_number").annotate(
            total_links=Count("id"),
            shared_links=Count("id", filter=Q(shared_at__isnull=False)),
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
    conf_counts = dict(
        confs_qs.values("dealer__assigned_rm_id")
        .annotate(confirmed=Count("id"))
        .values_list("dealer__assigned_rm_id", "confirmed")
    )

    headers = ["RM Name", "RM Mobile", "Total Links", "Links Shared", "Confirmed", "Pending", "Expired", "Conversion %"]
    rows = []
    for rm_id, st in link_stats.items():
        confirmed = conf_counts.get(rm_id, 0)
        total = st["total_links"]
        rows.append(
            {
                "RM Name": st["assigned_rm__full_name"],
                "RM Mobile": st["assigned_rm__mobile_number"],
                "Total Links": total,
                "Links Shared": st["shared_links"],
                "Confirmed": confirmed,
                "Pending": st["pending_links"],
                "Expired": st["expired_links"],
                "Conversion %": round((confirmed / total) * 100, 1) if total else 0.0,
            }
        )
    return headers, rows


def build_campaign_wise_report(user: User, filters: dict) -> tuple[list[str], list[dict]]:
    links_qs = _filter_links(user, filters)
    confs_qs = _filter_confirmations(user, filters).filter(submission_status=ConfirmationStatus.CONFIRMED)

    link_stats = {
        row["campaign_id"]: row
        for row in links_qs.values("campaign_id", "campaign__campaign_name", "campaign__campaign_code").annotate(
            total_links=Count("id"),
            shared_links=Count("id", filter=Q(shared_at__isnull=False)),
        )
    }
    conf_counts = dict(
        confs_qs.values("campaign_id")
        .annotate(confirmed=Count("id"))
        .values_list("campaign_id", "confirmed")
    )

    headers = ["Campaign Name", "Campaign Code", "Total Links", "Links Shared", "Confirmed", "Conversion %"]
    rows = []
    for cid, st in link_stats.items():
        confirmed = conf_counts.get(cid, 0)
        total = st["total_links"]
        rows.append(
            {
                "Campaign Name": st["campaign__campaign_name"],
                "Campaign Code": st["campaign__campaign_code"],
                "Total Links": total,
                "Links Shared": st["shared_links"],
                "Confirmed": confirmed,
                "Conversion %": round((confirmed / total) * 100, 1) if total else 0.0,
            }
        )
    return headers, rows


def build_date_wise_report(user: User, filters: dict) -> tuple[list[str], list[dict]]:
    qs = _filter_confirmations(user, filters).filter(submission_status=ConfirmationStatus.CONFIRMED)
    headers = ["Preferred Date", "Confirmed Bookings"]
    rows = [
        {
            "Preferred Date": row["preferred_date"].isoformat(),
            "Confirmed Bookings": row["count"],
        }
        for row in qs.values("preferred_date").annotate(count=Count("id")).order_by("preferred_date")
    ]
    return headers, rows


def build_time_slot_report(user: User, filters: dict) -> tuple[list[str], list[dict]]:
    qs = _filter_confirmations(user, filters).filter(submission_status=ConfirmationStatus.CONFIRMED)
    counts = dict(
        qs.values("preferred_time_slot_id")
        .annotate(booked=Count("id"))
        .values_list("preferred_time_slot_id", "booked")
    )
    headers = ["Time Slot", "Max Capacity (Per Day)", "Total Confirmed Bookings", "Active"]
    rows = [
        {
            "Time Slot": slot.display_label,
            "Max Capacity (Per Day)": slot.max_capacity,
            "Total Confirmed Bookings": counts.get(slot.id, 0),
            "Active": "Yes" if slot.is_active else "No",
        }
        for slot in TimeSlot.objects.all().order_by("start_time")
    ]
    return headers, rows


def build_link_usage_report(user: User, filters: dict) -> tuple[list[str], list[dict]]:
    headers = [
        "Dealer Code",
        "Campaign",
        "Assigned RM",
        "Allowed Month",
        "Status",
        "Submissions",
        "Shared At",
        "Expires At",
    ]
    rows = [
        {
            "Dealer Code": lnk.dealer.dealer_code,
            "Campaign": lnk.campaign.campaign_name,
            "Assigned RM": lnk.assigned_rm.full_name,
            "Allowed Month": lnk.allowed_month,
            "Status": lnk.status,
            "Submissions": f"{lnk.submission_count}/{lnk.max_submissions}",
            "Shared At": lnk.shared_at.strftime("%Y-%m-%d %H:%M") if lnk.shared_at else "",
            "Expires At": lnk.expires_at.strftime("%Y-%m-%d %H:%M"),
        }
        for lnk in _filter_links(user, filters)
    ]
    return headers, rows


REPORT_REGISTRY = {
    "dealer_master": ("Dealer Master Report", build_dealer_master_report),
    "confirmations": ("Confirmation Report", build_confirmation_report),
    "pending": ("Pending Dealer Report", build_pending_dealer_report),
    "rm_performance": ("RM-wise Report", build_rm_wise_report),
    "campaign_wise": ("Campaign-wise Report", build_campaign_wise_report),
    "date_wise": ("Date-wise Report", build_date_wise_report),
    "time_slot": ("Time-slot Report", build_time_slot_report),
    "link_usage": ("Link Usage Report", build_link_usage_report),
}
