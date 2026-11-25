"""Automated tests for Phase 11: Real-Time Admin Dashboard KPIs, Analytics & RBAC Scoping."""
from datetime import date, timedelta

from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone
import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
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
def dashboard_env(db):
    call_command("seed_rbac")
    roles = {r.code: r for r in Role.objects.all()}

    admin = User.objects.create_user("9800040001", "Dash Admin", "AdminPass@123")
    UserRole.objects.create(user=admin, role=roles["admin"])

    rm1 = User.objects.create_user("9800040002", "RM Dash 1", "RmPass@123")
    UserRole.objects.create(user=rm1, role=roles["rm"])

    rm2 = User.objects.create_user("9800040003", "RM Dash 2", "RmPass@123")
    UserRole.objects.create(user=rm2, role=roles["rm"])

    d1 = Dealer.objects.create(dealer_code="DSH-1", mobile_number="9876540001", assigned_rm=rm1)
    d2 = Dealer.objects.create(dealer_code="DSH-2", mobile_number="9876540002", assigned_rm=rm2)

    camp = Campaign.objects.create(
        campaign_name="Dashboard Campaign",
        campaign_code="DASH-2026",
        start_date=date(2026, 11, 1),
        end_date=date(2026, 11, 30),
    )
    slots = generate_time_slots_from_config()

    now = timezone.now()
    link1 = ConfirmationLink.objects.create(
        dealer=d1,
        token_hash=hash_token(generate_secure_token()),
        campaign=camp,
        created_by=rm1,
        assigned_rm=rm1,
        allowed_month="2026-11",
        shared_at=now,
        expires_at=now + timedelta(days=5),
        status=ConfirmationLinkStatus.USED,
        submission_count=1,
    )
    # Link 2 is pending & shared for RM2
    ConfirmationLink.objects.create(
        dealer=d2,
        token_hash=hash_token(generate_secure_token()),
        campaign=camp,
        created_by=rm2,
        assigned_rm=rm2,
        allowed_month="2026-11",
        shared_at=now,
        expires_at=now + timedelta(days=5),
        status=ConfirmationLinkStatus.SHARED,
    )

    Confirmation.objects.create(
        dealer=d1,
        confirmation_link=link1,
        campaign=camp,
        preferred_date=date.today() + timedelta(days=2),
        preferred_time_slot=slots[0],
        submission_status=ConfirmationStatus.CONFIRMED,
        submitted_at=now,
    )

    return {"admin": admin, "rm1": rm1, "rm2": rm2, "camp": camp}


@pytest.mark.django_db
class TestDashboardKPIsAndAnalytics:
    def test_admin_sees_org_wide_kpis_and_analytics_while_rm_sees_scoped_data(self, dashboard_env):
        admin_client = APIClient()
        admin_client.force_authenticate(user=dashboard_env["admin"])

        ov = admin_client.get(reverse("dashboard-overview")).data["data"]
        assert ov["total_dealers"] == 2
        assert ov["total_confirmation_links"] == 2
        assert ov["links_shared"] == 2
        assert ov["confirmations_received"] == 1
        assert ov["pending_confirmations"] == 1
        assert ov["upcoming_bookings"] == 1

        an = admin_client.get(reverse("dashboard-analytics")).data["data"]
        assert len(an["rm_performance"]) == 2
        assert len(an["campaign_performance"]) == 1
        assert len(an["time_slot_utilization"]) == 8
        assert an["pending_vs_confirmed"]["confirmed"] == 1
        assert an["pending_vs_confirmed"]["pending"] == 1

        # RM1 sees ONLY RM1's dealer (1 dealer, 1 link, 1 confirmed, 0 pending)
        rm1_client = APIClient()
        rm1_client.force_authenticate(user=dashboard_env["rm1"])
        rm1_ov = rm1_client.get(reverse("dashboard-overview")).data["data"]
        assert rm1_ov["total_dealers"] == 1
        assert rm1_ov["total_confirmation_links"] == 1
        assert rm1_ov["confirmations_received"] == 1
        assert rm1_ov["pending_confirmations"] == 0
