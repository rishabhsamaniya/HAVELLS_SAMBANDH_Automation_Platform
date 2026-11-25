"""Automated tests for Phase 09: Campaign CRUD & Unique Confirmation Link Generation."""
from datetime import date, datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.core.management import call_command
from django.urls import reverse
import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.audit_logs.models import AuditLog
from apps.campaigns.models import Campaign
from apps.confirmations.models import ConfirmationLink, ConfirmationLinkStatus
from apps.dealers.models import Dealer, DealerStatus
from apps.roles.models import Role, UserRole
from apps.scheduling.services import generate_time_slots_from_config


@pytest.fixture
def link_env(db):
    call_command("seed_rbac")
    roles = {r.code: r for r in Role.objects.all()}

    admin = User.objects.create_user("9800020001", "Admin Link", "AdminPass@123")
    UserRole.objects.create(user=admin, role=roles["admin"])

    rm1 = User.objects.create_user("9800020002", "RM Alpha", "RmPass@123")
    UserRole.objects.create(user=rm1, role=roles["rm"])

    rm2 = User.objects.create_user("9800020003", "RM Beta", "RmPass@123")
    UserRole.objects.create(user=rm2, role=roles["rm"])

    dealer1 = Dealer.objects.create(dealer_code="DLR-A1", mobile_number="9876501111", assigned_rm=rm1)
    dealer2 = Dealer.objects.create(dealer_code="DLR-B1", mobile_number="9876502222", assigned_rm=rm2)
    inactive_dealer = Dealer.objects.create(
        dealer_code="DLR-INACT",
        mobile_number="9876503333",
        assigned_rm=rm1,
        status=DealerStatus.INACTIVE,
    )

    campaign = Campaign.objects.create(
        campaign_name="Sambandh Nov 2026",
        campaign_code="NOV-2026",
        start_date=date(2026, 11, 1),
        end_date=date(2026, 11, 30),
    )
    generate_time_slots_from_config()

    return {
        "admin": admin,
        "rm1": rm1,
        "rm2": rm2,
        "dealer1": dealer1,
        "dealer2": dealer2,
        "inactive_dealer": inactive_dealer,
        "campaign": campaign,
    }


@pytest.mark.django_db
class TestConfirmationLinkGeneration:
    @patch("apps.confirmations.services_links.get_authoritative_today", return_value=date(2026, 11, 23))
    @patch("apps.scheduling.selectors.get_authoritative_today", return_value=date(2026, 11, 23))
    def test_generate_link_stores_hash_only_and_works_on_public_endpoint(self, _m1, _m2, link_env):
        client = APIClient()
        client.force_authenticate(user=link_env["rm1"])

        res = client.post(
            reverse("confirmation-links-list-create"),
            {
                "dealer": str(link_env["dealer1"].id),
                "campaign": str(link_env["campaign"].id),
            },
            format="json",
        )
        assert res.status_code == 201
        data = res.data["data"]
        assert data["allowed_month"] == "2026-11"
        assert "/confirm/" in data["shareable_url"]
        raw_token = data["shareable_url"].split("/confirm/")[1]

        # Raw token is NOT stored in DB or AuditLog
        link = ConfirmationLink.objects.get(id=data["id"])
        assert link.token_hash != raw_token
        assert len(link.token_hash) == 64
        audit = AuditLog.objects.get(action="CONFIRMATION_LINK_GENERATED", object_id=str(link.id))
        assert raw_token not in str(audit.new_values)

        # Public endpoint validates the generated token without authentication
        public_res = APIClient().get(reverse("public-confirm-detail", args=[raw_token]))
        assert public_res.status_code == 200
        assert public_res.data["data"]["allowed_month"] == "2026-11"

        # Mark as shared
        share_res = client.post(reverse("confirmation-links-mark-shared", args=[link.id]))
        assert share_res.status_code == 200
        assert share_res.data["data"]["status"] == "shared"
        assert share_res.data["data"]["shared_at"] is not None

        # Deactivating immediately blocks public link access
        deact_res = client.post(reverse("confirmation-links-deactivate", args=[link.id]))
        assert deact_res.status_code == 200
        assert APIClient().get(reverse("public-confirm-detail", args=[raw_token])).status_code == 410

    @patch("apps.confirmations.services_links.get_authoritative_today", return_value=date(2026, 11, 23))
    def test_auto_revokes_prior_unused_link_and_blocks_cross_rm_and_inactive_dealer(self, _m, link_env):
        client = APIClient()
        client.force_authenticate(user=link_env["rm1"])

        # Generate first link
        first = client.post(
            reverse("confirmation-links-list-create"),
            {"dealer": str(link_env["dealer1"].id), "campaign": str(link_env["campaign"].id)},
            format="json",
        )
        assert first.status_code == 201
        first_id = first.data["data"]["id"]

        # Generate second link -> first is automatically deactivated
        second = client.post(
            reverse("confirmation-links-list-create"),
            {"dealer": str(link_env["dealer1"].id), "campaign": str(link_env["campaign"].id)},
            format="json",
        )
        assert second.status_code == 201
        assert ConfirmationLink.objects.get(id=first_id).status == ConfirmationLinkStatus.DEACTIVATED

        # RM1 cannot generate link for RM2's dealer
        cross_rm = client.post(
            reverse("confirmation-links-list-create"),
            {"dealer": str(link_env["dealer2"].id), "campaign": str(link_env["campaign"].id)},
            format="json",
        )
        assert cross_rm.status_code == 403

        # Inactive dealer rejected
        inact = client.post(
            reverse("confirmation-links-list-create"),
            {"dealer": str(link_env["inactive_dealer"].id), "campaign": str(link_env["campaign"].id)},
            format="json",
        )
        assert inact.status_code == 400
        assert inact.data["error"]["code"] == "DEALER_INACTIVE"

        # Custom expiry beyond allowed_month rejected
        bad_exp = client.post(
            reverse("confirmation-links-list-create"),
            {
                "dealer": str(link_env["dealer1"].id),
                "campaign": str(link_env["campaign"].id),
                "expires_at": datetime(2026, 12, 5, 12, 0, tzinfo=ZoneInfo("Asia/Kolkata")).isoformat(),
            },
            format="json",
        )
        assert bad_exp.status_code == 400
        assert bad_exp.data["error"]["code"] == "EXPIRY_EXCEEDS_ALLOWED_MONTH"

    @patch("apps.confirmations.services_links.get_authoritative_today", return_value=date(2026, 11, 23))
    @patch("apps.confirmations.services.get_authoritative_today", return_value=date(2026, 11, 23))
    @patch("apps.scheduling.selectors.get_authoritative_today", return_value=date(2026, 11, 23))
    def test_bulk_generate_copy_share_auto_count_and_regenerate_dashboard_summary(
        self, _m1, _m2, _m3, link_env
    ):
        # Add a second dealer for RM1 so RM1 can bulk-generate
        dealer1b = Dealer.objects.create(
            dealer_code="DLR-A2",
            mobile_number="9876501112",
            assigned_rm=link_env["rm1"],
        )
        rm1_client = APIClient()
        rm1_client.force_authenticate(user=link_env["rm1"])

        # 1. Bulk generate for all active RM1 dealers (RM2's dealer2 is excluded automatically)
        bulk_res = rm1_client.post(
            reverse("confirmation-links-bulk-generate"),
            {"campaign": str(link_env["campaign"].id), "select_all_active": True},
            format="json",
        )
        assert bulk_res.status_code == 201
        assert bulk_res.data["data"]["created_count"] == 2
        assert bulk_res.data["data"]["skipped_count"] == 0
        link_a1_id = next(
            l["id"] for l in bulk_res.data["data"]["links"] if l["dealer_code"] == "DLR-A1"
        )
        link_a2 = next(
            l for l in bulk_res.data["data"]["links"] if l["dealer_code"] == "DLR-A2"
        )

        # 2. Running bulk generate again skips both existing dealers (zero duplicates!)
        bulk_again = rm1_client.post(
            reverse("confirmation-links-bulk-generate"),
            {"campaign": str(link_env["campaign"].id), "dealer_ids": [str(link_env["dealer1"].id), str(dealer1b.id)]},
            format="json",
        )
        assert bulk_again.status_code == 201
        assert bulk_again.data["data"]["created_count"] == 0
        assert bulk_again.data["data"]["skipped_count"] == 2

        # 3. Copy-share anytime decrypts valid URL & auto-increments Dashboard 'links_shared'
        copy_res = rm1_client.post(reverse("confirmation-links-copy-share", args=[link_a1_id]))
        assert copy_res.status_code == 200
        assert copy_res.data["data"]["status"] == "shared"
        share_url = copy_res.data["data"]["shareable_url"]
        share_msg = copy_res.data["data"]["share_message"]
        assert f"Link: {share_url}" in share_msg
        assert "Greetings from Havells Sambandh Surprises." in share_msg
        assert "Regards,\nHavells Sambandh Surprises" in share_msg
        copied_token = share_url.split("/confirm/")[1]
        assert APIClient().get(reverse("public-confirm-detail", args=[copied_token])).status_code == 200

        dash1 = rm1_client.get(reverse("dashboard-overview")).data["data"]
        assert dash1["links_shared"] == 1
        assert dash1["regenerated_links"] == 0

        # 4. Submitting link_a2 directly (without clicking copy) also auto-increments 'links_shared'
        raw_token_a2 = link_a2["shareable_url"].split("/confirm/")[1]
        avail = APIClient().get(
            reverse("public-confirm-availability", args=[raw_token_a2]) + "?date=2026-11-24"
        )
        slot_id = avail.data["data"]["slots"][0]["id"]
        sub_res = APIClient().post(
            reverse("public-confirm-submit", args=[raw_token_a2]),
            {
                "dealer_code": "DLR-A2",
                "mobile_number": "9876501112",
                "preferred_date": "2026-11-24",
                "preferred_time_slot": slot_id,
            },
            format="json",
        )
        assert sub_res.status_code == 201
        dash2 = rm1_client.get(reverse("dashboard-overview")).data["data"]
        assert dash2["links_shared"] == 2

        # 5. Regenerate link_a1 IN PLACE -> NO duplicate row, old token invalid, RM-wise count increments!
        regen_res = rm1_client.post(reverse("confirmation-links-regenerate", args=[link_a1_id]))
        assert regen_res.status_code == 200
        assert regen_res.data["data"]["id"] == link_a1_id
        assert regen_res.data["data"]["is_regenerated"] is True
        assert regen_res.data["data"]["regeneration_count"] == 1
        assert ConfirmationLink.objects.filter(dealer=link_env["dealer1"]).count() == 1

        # Old token immediately stops working; new token works
        assert APIClient().get(reverse("public-confirm-detail", args=[copied_token])).status_code == 404
        new_token_1 = regen_res.data["data"]["shareable_url"].split("/confirm/")[1]
        assert APIClient().get(reverse("public-confirm-detail", args=[new_token_1])).status_code == 200

        # Regenerate a 2nd time -> still 1 single row, Dashboard & RM-wise regenerated count becomes 2
        regen_res_2 = rm1_client.post(reverse("confirmation-links-regenerate", args=[link_a1_id]))
        assert regen_res_2.status_code == 200
        assert regen_res_2.data["data"]["regeneration_count"] == 2
        assert ConfirmationLink.objects.filter(dealer=link_env["dealer1"]).count() == 1

        dash3 = rm1_client.get(reverse("dashboard-overview")).data["data"]
        assert dash3["total_confirmation_links"] == 2
        assert dash3["regenerated_links"] == 2

        an = rm1_client.get(reverse("dashboard-analytics")).data["data"]
        assert an["rm_performance"][0]["regenerated_links"] == 2
