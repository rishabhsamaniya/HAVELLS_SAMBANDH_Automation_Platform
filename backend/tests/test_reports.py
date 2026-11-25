"""Automated tests for Phase 12: 8 Reports, Excel/CSV Export & RBAC/RM Scoping."""
from datetime import date, timedelta

from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone
import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.audit_logs.models import AuditLog
from apps.campaigns.models import Campaign
from apps.confirmations.models import (
    Confirmation,
    ConfirmationLink,
    ConfirmationLinkStatus,
    ConfirmationStatus,
)
from apps.dealers.models import Dealer
from apps.roles.models import Role, UserRole
from apps.scheduling.services import generate_time_slots_from_config
from services.tokens import generate_secure_token, hash_token


@pytest.fixture
def report_env(db):
    call_command("seed_rbac")
    roles = {r.code: r for r in Role.objects.all()}

    admin = User.objects.create_user("9800050001", "Rpt Admin", "AdminPass@123")
    UserRole.objects.create(user=admin, role=roles["admin"])

    rm1 = User.objects.create_user("9800050002", "RM Rpt 1", "RmPass@123")
    UserRole.objects.create(user=rm1, role=roles["rm"])

    rm2 = User.objects.create_user("9800050003", "RM Rpt 2", "RmPass@123")
    UserRole.objects.create(user=rm2, role=roles["rm"])

    no_role_user = User.objects.create_user("9800050004", "No Role", "Pass@1234")

    d1 = Dealer.objects.create(dealer_code="RPT-D1", mobile_number="9876550001", assigned_rm=rm1)
    d2 = Dealer.objects.create(dealer_code="RPT-D2", mobile_number="9876550002", assigned_rm=rm2)

    camp = Campaign.objects.create(
        campaign_name="Report Campaign",
        campaign_code="RPT-2026",
        start_date=date(2026, 11, 1),
        end_date=date(2026, 11, 30),
    )
    slots = generate_time_slots_from_config()
    now = timezone.now()

    l1 = ConfirmationLink.objects.create(
        dealer=d1,
        token_hash=hash_token(generate_secure_token()),
        campaign=camp,
        assigned_rm=rm1,
        allowed_month="2026-11",
        expires_at=now + timedelta(days=5),
        status=ConfirmationLinkStatus.USED,
        submission_count=1,
    )
    ConfirmationLink.objects.create(
        dealer=d2,
        token_hash=hash_token(generate_secure_token()),
        campaign=camp,
        assigned_rm=rm2,
        allowed_month="2026-11",
        expires_at=now + timedelta(days=5),
        status=ConfirmationLinkStatus.SHARED,
    )
    Confirmation.objects.create(
        dealer=d1,
        confirmation_link=l1,
        campaign=camp,
        preferred_date=date(2026, 11, 25),
        preferred_time_slot=slots[0],
        submission_status=ConfirmationStatus.CONFIRMED,
        submitted_at=now,
    )

    return {"admin": admin, "rm1": rm1, "rm2": rm2, "no_role": no_role_user}


@pytest.mark.django_db
class TestReportingAndExports:
    def test_all_eight_report_endpoints_succeed_for_admin(self, report_env):
        client = APIClient()
        client.force_authenticate(user=report_env["admin"])

        url_names = [
            "reports-dealer-master",
            "reports-confirmations",
            "reports-pending",
            "reports-rm-performance",
            "reports-campaign-wise",
            "reports-date-wise",
            "reports-time-slot",
            "reports-link-usage",
        ]
        for name in url_names:
            res = client.get(reverse(name))
            assert res.status_code == 200, f"Report {name} failed"
            assert "headers" in res.data["data"]
            assert "rows" in res.data["data"]

    def test_excel_and_csv_exports_enforce_permissions_and_rm_isolation(self, report_env):
        # User without reports.export -> 403
        unauth = APIClient()
        unauth.force_authenticate(user=report_env["no_role"])
        assert unauth.get(reverse("reports-export") + "?report=dealer_master&format=xlsx").status_code == 403

        # Admin Excel export succeeds and logs audit event
        admin_client = APIClient()
        admin_client.force_authenticate(user=report_env["admin"])
        xlsx_res = admin_client.get(reverse("reports-export") + "?report=confirmations&format=xlsx")
        assert xlsx_res.status_code == 200
        assert "spreadsheetml" in xlsx_res["Content-Type"]
        assert AuditLog.objects.filter(action="REPORT_EXPORTED", object_id="confirmations").exists()

        # RM1 CSV export includes ONLY RPT-D1 and NOT RPT-D2
        rm1_client = APIClient()
        rm1_client.force_authenticate(user=report_env["rm1"])
        csv_res = rm1_client.get(reverse("reports-export") + "?report=dealer_master&format=csv")
        assert csv_res.status_code == 200
        text = csv_res.content.decode("utf-8")
        assert "RPT-D1" in text
        assert "RPT-D2" not in text
