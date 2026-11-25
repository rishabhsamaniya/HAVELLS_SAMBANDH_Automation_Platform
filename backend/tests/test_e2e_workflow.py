"""End-to-End Integration Test covering the complete Havells Sambandh lifecycle."""
from datetime import date
from unittest.mock import patch

from django.core.management import call_command
from django.urls import reverse
import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.confirmations.services import APPROVED_SUCCESS_MESSAGE
from apps.roles.models import Role, UserRole
from apps.scheduling.services import generate_time_slots_from_config


@pytest.mark.django_db
class TestCompleteEndToEndWorkflow:
    @patch("apps.confirmations.services_links.get_authoritative_today", return_value=date(2026, 11, 23))
    @patch("apps.confirmations.services.get_authoritative_today", return_value=date(2026, 11, 23))
    @patch("apps.scheduling.selectors.get_authoritative_today", return_value=date(2026, 11, 23))
    def test_full_admin_to_dealer_to_dashboard_workflow(self, _m1, _m2, _m3):
        call_command("seed_rbac")
        roles = {r.code: r for r in Role.objects.all()}
        generate_time_slots_from_config()

        admin = User.objects.create_superuser("9876000001", "E2E Admin", "AdminPass@123")
        UserRole.objects.create(user=admin, role=roles["super_admin"])

        # 1. Admin Login
        admin_client = APIClient()
        login_res = admin_client.post(
            reverse("auth-login"),
            {"mobile_number": "9876000001", "password": "AdminPass@123"},
            format="json",
        )
        assert login_res.status_code == 200
        access = login_res.data["data"]["access"]
        admin_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        # 2. Create RM
        rm_res = admin_client.post(
            reverse("users-list-create"),
            {
                "full_name": "E2E Field RM",
                "mobile_number": "9876000002",
                "password": "RmPassword@123",
                "role_ids": [str(roles["rm"].id)],
            },
            format="json",
        )
        assert rm_res.status_code == 201
        rm_id = rm_res.data["data"]["id"]

        # 3. Create Campaign
        camp_res = admin_client.post(
            reverse("campaigns-list-create"),
            {
                "campaign_name": "Sambandh E2E Nov 2026",
                "campaign_code": "E2E-NOV-2026",
                "start_date": "2026-11-01",
                "end_date": "2026-11-30",
            },
            format="json",
        )
        assert camp_res.status_code == 201
        camp_id = camp_res.data["data"]["id"]

        # 4. Create Dealer & Assign to RM
        dealer_res = admin_client.post(
            reverse("dealers-list-create"),
            {
                "dealer_code": "HVL-E2E-01",
                "mobile_number": "9876000099",
                "assigned_rm": rm_id,
            },
            format="json",
        )
        assert dealer_res.status_code == 201
        dealer_id = dealer_res.data["data"]["id"]

        # 5. Generate Confirmation Link
        link_res = admin_client.post(
            reverse("confirmation-links-list-create"),
            {"dealer": dealer_id, "campaign": camp_id},
            format="json",
        )
        assert link_res.status_code == 201
        raw_token = link_res.data["data"]["shareable_url"].split("/confirm/")[1]

        # 6. Open Public Form (Zero Login)
        public_client = APIClient()
        meta_res = public_client.get(reverse("public-confirm-detail", args=[raw_token]))
        assert meta_res.status_code == 200
        chosen_date = meta_res.data["data"]["available_dates"][0]
        assert chosen_date == "2026-11-24"

        # 7. Fetch Available 1-Hour Slots
        slots_res = public_client.get(
            reverse("public-confirm-availability", args=[raw_token]) + f"?date={chosen_date}"
        )
        assert slots_res.status_code == 200
        chosen_slot_id = slots_res.data["data"]["slots"][0]["id"]

        # 8. Submit Public Form -> Verify Exact Approved Success Message
        submit_res = public_client.post(
            reverse("public-confirm-submit", args=[raw_token]),
            {
                "dealer_code": "HVL-E2E-01",
                "mobile_number": "9876000099",
                "preferred_date": chosen_date,
                "preferred_time_slot": chosen_slot_id,
            },
            format="json",
        )
        assert submit_res.status_code == 201
        assert submit_res.data["message"] == APPROVED_SUCCESS_MESSAGE

        # 9. Admin Dashboard Immediately Reflects the Confirmation
        dash_res = admin_client.get(reverse("dashboard-overview"))
        assert dash_res.status_code == 200
        assert dash_res.data["data"]["total_dealers"] == 1
        assert dash_res.data["data"]["total_confirmation_links"] == 1
        assert dash_res.data["data"]["confirmations_received"] == 1
        assert dash_res.data["data"]["pending_confirmations"] == 0
