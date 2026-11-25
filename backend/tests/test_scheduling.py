"""Automated tests for Phase 10: Scheduling Management, Holidays, Blocking, Reschedule & Cancel."""
from datetime import date

from django.core.management import call_command
from django.urls import reverse
import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.audit_logs.models import AuditLog
from apps.campaigns.models import Campaign
from apps.dealers.models import Dealer
from apps.roles.models import Role, UserRole
from apps.scheduling.services import generate_time_slots_from_config


@pytest.fixture
def sched_env(db):
    call_command("seed_rbac")
    roles = {r.code: r for r in Role.objects.all()}

    admin = User.objects.create_user("9800030001", "Sched Admin", "AdminPass@123")
    UserRole.objects.create(user=admin, role=roles["admin"])

    rm1 = User.objects.create_user("9800030002", "RM Sched 1", "RmPass@123")
    UserRole.objects.create(user=rm1, role=roles["rm"])

    rm2 = User.objects.create_user("9800030003", "RM Sched 2", "RmPass@123")
    UserRole.objects.create(user=rm2, role=roles["rm"])

    dealer1 = Dealer.objects.create(dealer_code="SCH-D1", mobile_number="9876510001", assigned_rm=rm1)
    dealer2 = Dealer.objects.create(dealer_code="SCH-D2", mobile_number="9876510002", assigned_rm=rm2)

    campaign = Campaign.objects.create(
        campaign_name="Sambandh Sched Camp",
        campaign_code="SCH-2026",
        start_date=date(2026, 11, 1),
        end_date=date(2026, 11, 30),
    )
    slots = generate_time_slots_from_config()

    return {
        "admin": admin,
        "rm1": rm1,
        "rm2": rm2,
        "dealer1": dealer1,
        "dealer2": dealer2,
        "campaign": campaign,
        "slots": slots,
    }


@pytest.mark.django_db
class TestSchedulingManagement:
    def test_operating_hours_slot_update_holiday_and_block_unblock(self, sched_env):
        client = APIClient()
        client.force_authenticate(user=sched_env["admin"])

        # Update slot capacity
        slot = sched_env["slots"][0]
        assert len(sched_env["slots"]) == 24
        assert sched_env["slots"][0].display_label == "12:00 AM – 01:00 AM"
        assert sched_env["slots"][-1].display_label == "11:00 PM – 12:00 AM"

        # Configure 24-hour operating hours (00:00 to 00:00) via API
        cfg_res = client.post(
            reverse("scheduling-config"),
            {
                "opening_time": "00:00",
                "closing_time": "00:00",
                "slot_duration": 60,
                "default_capacity": 1,
                "allow_same_day_booking": False,
            },
            format="json",
        )
        assert cfg_res.status_code == 200
        slots_res = client.get(reverse("scheduling-slots"))
        assert slots_res.status_code == 200
        assert len(slots_res.data["data"]) == 24

        patch_res = client.patch(
            reverse("scheduling-slot-update", args=[slot.id]),
            {"max_capacity": 2},
            format="json",
        )
        assert patch_res.status_code == 200
        assert patch_res.data["data"]["max_capacity"] == 2

        # Block slot on 2026-11-25
        blk_res = client.post(
            reverse("scheduling-blocked-slots"),
            {"date": "2026-11-25", "time_slot": str(slot.id), "reason": "Audit Review"},
            format="json",
        )
        assert blk_res.status_code == 201
        blocked_id = blk_res.data["data"]["id"]

        # Internal availability reflects blocked slot (remaining_capacity == 0)
        avail = client.get(reverse("scheduling-availability") + "?date=2026-11-25")
        assert avail.status_code == 200
        slot_entry = next(s for s in avail.data["data"]["slots"] if s["id"] == str(slot.id))
        assert slot_entry["is_blocked"] is True
        assert slot_entry["remaining_capacity"] == 0

        # Unblock restores capacity
        assert client.delete(reverse("scheduling-blocked-slot-delete", args=[blocked_id])).status_code == 200
        avail2 = client.get(reverse("scheduling-availability") + "?date=2026-11-25")
        slot_entry2 = next(s for s in avail2.data["data"]["slots"] if s["id"] == str(slot.id))
        assert slot_entry2["is_blocked"] is False
        assert slot_entry2["remaining_capacity"] == 2

    def test_manual_booking_reschedule_cancel_and_rm_isolation(self, sched_env):
        admin_client = APIClient()
        admin_client.force_authenticate(user=sched_env["admin"])

        slot1 = sched_env["slots"][0]
        slot2 = sched_env["slots"][1]

        # Admin creates manual booking for Dealer 1 (assigned to RM1) on slot1
        create_res = admin_client.post(
            reverse("scheduling-bookings"),
            {
                "dealer": str(sched_env["dealer1"].id),
                "campaign": str(sched_env["campaign"].id),
                "preferred_date": "2026-11-24",
                "preferred_time_slot": str(slot1.id),
            },
            format="json",
        )
        assert create_res.status_code == 201
        booking_id = create_res.data["data"]["id"]

        # RM2 cannot reschedule RM1's dealer booking (404 due to queryset scoping)
        rm2_client = APIClient()
        rm2_client.force_authenticate(user=sched_env["rm2"])
        assert (
            rm2_client.post(
                reverse("scheduling-booking-reschedule", args=[booking_id]),
                {"preferred_date": "2026-11-25", "preferred_time_slot": str(slot2.id)},
                format="json",
            ).status_code
            == 404
        )

        # RM1 CAN reschedule own dealer's booking to slot2 -> releases slot1!
        rm1_client = APIClient()
        rm1_client.force_authenticate(user=sched_env["rm1"])
        resched = rm1_client.post(
            reverse("scheduling-booking-reschedule", args=[booking_id]),
            {
                "preferred_date": "2026-11-25",
                "preferred_time_slot": str(slot2.id),
                "reason": "Dealer requested next day",
            },
            format="json",
        )
        assert resched.status_code == 200
        assert resched.data["data"]["preferred_date"] == "2026-11-25"
        assert AuditLog.objects.filter(action="BOOKING_RESCHEDULED", object_id=booking_id).exists()

        # History shows Created + Rescheduled
        hist = rm1_client.get(reverse("scheduling-booking-history", args=[booking_id]))
        assert hist.status_code == 200
        assert len(hist.data["data"]) == 2

        # Cancel booking releases slot2 capacity
        cancel = rm1_client.post(
            reverse("scheduling-booking-cancel", args=[booking_id]),
            {"reason": "Dealer unavailable"},
            format="json",
        )
        assert cancel.status_code == 200
        assert cancel.data["data"]["submission_status"] == "cancelled"

        # Now Dealer 2 can book slot2 on 2026-11-25
        rebook = admin_client.post(
            reverse("scheduling-bookings"),
            {
                "dealer": str(sched_env["dealer2"].id),
                "campaign": str(sched_env["campaign"].id),
                "preferred_date": "2026-11-25",
                "preferred_time_slot": str(slot2.id),
            },
            format="json",
        )
        assert rebook.status_code == 201
        rebook_id = rebook.data["data"]["id"]

        # Action options endpoint exposes 3 experience actions with 6 action-based remarks each
        opts = admin_client.get(reverse("scheduling-booking-action-options"))
        assert opts.status_code == 200
        actions = opts.data["data"]["actions"]
        remarks_map = opts.data["data"]["remarks_by_action"]
        assert [a["value"] for a in actions] == [
            "experience_completed",
            "experience_on_hold",
            "experience_postponed",
        ]
        for action_key in ["experience_completed", "experience_on_hold", "experience_postponed"]:
            assert len(remarks_map[action_key]) == 6

        # Reject mismatched remark for chosen action
        bad_status = admin_client.post(
            reverse("scheduling-booking-status", args=[rebook_id]),
            {
                "action": "experience_completed",
                "remarks": remarks_map["experience_on_hold"][0],
            },
            format="json",
        )
        assert bad_status.status_code == 400

        # Valid Experience Completed status + remark persists and writes audit log
        good_status = admin_client.post(
            reverse("scheduling-booking-status", args=[rebook_id]),
            {
                "action": "experience_completed",
                "remarks": remarks_map["experience_completed"][0],
            },
            format="json",
        )
        assert good_status.status_code == 200
        assert good_status.data["data"]["submission_status"] == "experience_completed"
        assert good_status.data["data"]["remarks"] == remarks_map["experience_completed"][0]
        assert AuditLog.objects.filter(action="BOOKING_STATUS_UPDATED", object_id=rebook_id).exists()
