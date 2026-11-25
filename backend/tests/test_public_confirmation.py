"""Automated tests for Phase 08: Public Dealer Date Confirmation Form & Atomic Booking."""
from datetime import date, datetime, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.urls import reverse
from django.utils import timezone
import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.audit_logs.models import AuditLog
from apps.campaigns.models import Campaign
from apps.confirmations.models import (
    Confirmation,
    ConfirmationHistory,
    ConfirmationLink,
    ConfirmationLinkStatus,
)
from apps.confirmations.services import APPROVED_SUCCESS_MESSAGE
from apps.dealers.models import Dealer
from apps.scheduling.models import BlockedSlot, Holiday
from apps.scheduling.services import generate_time_slots_from_config
from services.tokens import generate_secure_token, hash_token


@pytest.fixture
def confirmation_setup(db):
    rm = User.objects.create_user("9800010001", "RM North", "RmPass@123")
    dealer1 = Dealer.objects.create(dealer_code="HVL-D01", mobile_number="9876543210", assigned_rm=rm)
    dealer2 = Dealer.objects.create(dealer_code="HVL-D02", mobile_number="9876543211", assigned_rm=rm)
    campaign = Campaign.objects.create(
        campaign_name="Sambandh Nov 2026",
        campaign_code="SAMBANDH-2026-11",
        start_date=date(2026, 11, 1),
        end_date=date(2026, 11, 30),
        timezone="Asia/Kolkata",
    )
    slots = generate_time_slots_from_config()

    raw_token1 = generate_secure_token()
    link1 = ConfirmationLink.objects.create(
        dealer=dealer1,
        token_hash=hash_token(raw_token1),
        campaign=campaign,
        created_by=rm,
        assigned_rm=rm,
        allowed_month="2026-11",
        expires_at=datetime(2026, 11, 30, 23, 59, 59, tzinfo=ZoneInfo("Asia/Kolkata")),
        status=ConfirmationLinkStatus.SHARED,
    )

    raw_token2 = generate_secure_token()
    link2 = ConfirmationLink.objects.create(
        dealer=dealer2,
        token_hash=hash_token(raw_token2),
        campaign=campaign,
        created_by=rm,
        assigned_rm=rm,
        allowed_month="2026-11",
        expires_at=datetime(2026, 11, 30, 23, 59, 59, tzinfo=ZoneInfo("Asia/Kolkata")),
        status=ConfirmationLinkStatus.SHARED,
    )

    return {
        "rm": rm,
        "dealer1": dealer1,
        "dealer2": dealer2,
        "campaign": campaign,
        "slots": slots,
        "token1": raw_token1,
        "link1": link1,
        "token2": raw_token2,
        "link2": link2,
    }


@pytest.mark.django_db
class TestPublicDealerConfirmation:
    @patch("apps.scheduling.selectors.get_authoritative_today", return_value=date(2026, 11, 23))
    @patch("apps.confirmations.services.get_authoritative_today", return_value=date(2026, 11, 23))
    def test_same_month_future_only_dates_and_no_internal_ids_exposed(
        self, _m1, _m2, confirmation_setup
    ):
        client = APIClient()
        res = client.get(reverse("public-confirm-detail", args=[confirmation_setup["token1"]]))
        assert res.status_code == 200
        data = res.data["data"]
        assert data["allowed_month"] == "2026-11"
        assert data["has_available_dates"] is True
        # Link on 23 Nov -> 24 Nov through 30 Nov allowed; 22 Nov, 23 Nov, 1 Dec excluded
        assert data["available_dates"][0] == "2026-11-24"
        assert data["available_dates"][-1] == "2026-11-30"
        assert "2026-11-23" not in data["available_dates"]
        assert "2026-12-01" not in data["available_dates"]
        # No internal IDs exposed
        assert "dealer_id" not in data
        assert "id" not in data

    @patch("apps.scheduling.selectors.get_authoritative_today", return_value=date(2026, 11, 30))
    @patch("apps.confirmations.services.get_authoritative_today", return_value=date(2026, 11, 30))
    def test_last_day_of_month_returns_no_available_dates(self, _m1, _m2, confirmation_setup):
        client = APIClient()
        res = client.get(reverse("public-confirm-detail", args=[confirmation_setup["token1"]]))
        assert res.status_code == 200
        assert res.data["data"]["has_available_dates"] is False
        assert res.data["data"]["available_dates"] == []

    @patch("apps.scheduling.selectors.get_authoritative_today", return_value=date(2026, 11, 23))
    @patch("apps.confirmations.services.get_authoritative_today", return_value=date(2026, 11, 23))
    def test_rejects_past_same_day_next_month_and_holiday_dates(
        self, _m1, _m2, confirmation_setup
    ):
        Holiday.objects.create(date=date(2026, 11, 26), name="Company Holiday")
        client = APIClient()
        slot_id = str(confirmation_setup["slots"][0].id)
        submit_url = reverse("public-confirm-submit", args=[confirmation_setup["token1"]])

        for bad_date, expected_code in [
            ("2026-11-22", "PAST_DATE_NOT_ALLOWED"),
            ("2026-11-23", "PAST_DATE_NOT_ALLOWED"),
            ("2026-12-01", "DATE_OUTSIDE_ALLOWED_MONTH"),
            ("2026-11-26", "DATE_IS_HOLIDAY"),
        ]:
            res = client.post(
                submit_url,
                {
                    "dealer_code": "HVL-D01",
                    "mobile_number": "9876543210",
                    "preferred_date": bad_date,
                    "preferred_time_slot": slot_id,
                },
                format="json",
            )
            assert res.status_code == 400
            assert res.data["error"]["code"] == expected_code

    @patch("apps.scheduling.selectors.get_authoritative_today", return_value=date(2026, 11, 23))
    @patch("apps.confirmations.services.get_authoritative_today", return_value=date(2026, 11, 23))
    def test_rejects_dealer_code_and_mobile_mismatch(self, _m1, _m2, confirmation_setup):
        client = APIClient()
        slot_id = str(confirmation_setup["slots"][0].id)
        submit_url = reverse("public-confirm-submit", args=[confirmation_setup["token1"]])

        bad_code = client.post(
            submit_url,
            {
                "dealer_code": "WRONG-99",
                "mobile_number": "9876543210",
                "preferred_date": "2026-11-24",
                "preferred_time_slot": slot_id,
            },
            format="json",
        )
        assert bad_code.status_code == 400
        assert bad_code.data["error"]["code"] == "INVALID_DEALER_CODE"

        bad_mob = client.post(
            submit_url,
            {
                "dealer_code": "HVL-D01",
                "mobile_number": "9999999999",
                "preferred_date": "2026-11-24",
                "preferred_time_slot": slot_id,
            },
            format="json",
        )
        assert bad_mob.status_code == 400
        assert bad_mob.data["error"]["code"] == "MOBILE_NUMBER_MISMATCH"

    @patch("apps.scheduling.selectors.get_authoritative_today", return_value=date(2026, 11, 23))
    @patch("apps.confirmations.services.get_authoritative_today", return_value=date(2026, 11, 23))
    def test_successful_submission_prevents_duplicate_and_prevents_overbooking(
        self, _m1, _m2, confirmation_setup
    ):
        client = APIClient()
        slot = confirmation_setup["slots"][0]
        assert slot.display_label == "10:00 AM – 11:00 AM"

        # Dealer 1 books 24 Nov 10:00-11:00 AM (capacity = 1)
        res1 = client.post(
            reverse("public-confirm-submit", args=[confirmation_setup["token1"]]),
            {
                "dealer_code": "hvl-d01",
                "mobile_number": "+91 9876543210",
                "preferred_date": "2026-11-24",
                "preferred_time_slot": str(slot.id),
            },
            format="json",
        )
        assert res1.status_code == 201
        assert res1.data["message"] == APPROVED_SUCCESS_MESSAGE
        assert res1.data["data"]["confirmation_message"] == APPROVED_SUCCESS_MESSAGE
        assert Confirmation.objects.count() == 1
        assert ConfirmationHistory.objects.count() == 1
        assert AuditLog.objects.filter(action="DEALER_CONFIRMATION_SUBMITTED").exists()

        # Duplicate submission on link 1 rejected
        dup = client.post(
            reverse("public-confirm-submit", args=[confirmation_setup["token1"]]),
            {
                "dealer_code": "HVL-D01",
                "mobile_number": "9876543210",
                "preferred_date": "2026-11-25",
                "preferred_time_slot": str(confirmation_setup["slots"][1].id),
            },
            format="json",
        )
        assert dup.status_code == 409
        assert dup.data["error"]["code"] == "DUPLICATE_SUBMISSION"

        # Dealer 2 attempting to book the ALREADY FULL slot on 24 Nov gets 409 TIME_SLOT_UNAVAILABLE
        overbook = client.post(
            reverse("public-confirm-submit", args=[confirmation_setup["token2"]]),
            {
                "dealer_code": "HVL-D02",
                "mobile_number": "9876543211",
                "preferred_date": "2026-11-24",
                "preferred_time_slot": str(slot.id),
            },
            format="json",
        )
        assert overbook.status_code == 409
        assert overbook.data["error"]["code"] == "TIME_SLOT_UNAVAILABLE"

        # Availability endpoint for 24 Nov no longer lists the booked slot
        avail = client.get(
            reverse("public-confirm-availability", args=[confirmation_setup["token2"]])
            + "?date=2026-11-24"
        )
        assert avail.status_code == 200
        returned_slot_ids = [s["id"] for s in avail.data["data"]["slots"]]
        assert str(slot.id) not in returned_slot_ids
        assert len(returned_slot_ids) == 7

    def test_expired_deactivated_and_invalid_links_rejected(self, confirmation_setup):
        client = APIClient()
        # Invalid token -> 404
        inv = client.get(reverse("public-confirm-detail", args=["nonexistent-token-xyz"]))
        assert inv.status_code == 404
        assert inv.data["error"]["code"] == "INVALID_CONFIRMATION_TOKEN"

        # Expired link -> 410
        link1 = confirmation_setup["link1"]
        link1.expires_at = timezone.now() - timedelta(hours=1)
        link1.save()
        exp = client.get(reverse("public-confirm-detail", args=[confirmation_setup["token1"]]))
        assert exp.status_code == 410
        assert exp.data["error"]["code"] == "LINK_EXPIRED"

        # Deactivated link -> 410
        link2 = confirmation_setup["link2"]
        link2.status = ConfirmationLinkStatus.DEACTIVATED
        link2.save()
        deact = client.get(reverse("public-confirm-detail", args=[confirmation_setup["token2"]]))
        assert deact.status_code == 410
        assert deact.data["error"]["code"] == "LINK_DEACTIVATED"

    @patch("apps.scheduling.selectors.get_authoritative_today", return_value=date(2026, 11, 23))
    @patch("apps.confirmations.services.get_authoritative_today", return_value=date(2026, 11, 23))
    def test_blocked_slot_cannot_be_booked(self, _m1, _m2, confirmation_setup):
        slot = confirmation_setup["slots"][2]
        BlockedSlot.objects.create(date=date(2026, 11, 25), time_slot=slot, reason="VIP Maintenance")
        client = APIClient()
        res = client.post(
            reverse("public-confirm-submit", args=[confirmation_setup["token1"]]),
            {
                "dealer_code": "HVL-D01",
                "mobile_number": "9876543210",
                "preferred_date": "2026-11-25",
                "preferred_time_slot": str(slot.id),
            },
            format="json",
        )
        assert res.status_code == 409
        assert res.data["error"]["code"] == "TIME_SLOT_UNAVAILABLE"
