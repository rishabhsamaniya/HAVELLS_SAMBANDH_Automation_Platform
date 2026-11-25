"""Automated tests for Phase 05: Authentication, Lockout, Password Reset & User Management."""
from django.core.management import call_command
from django.urls import reverse
import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.audit_logs.models import AuditLog
from apps.roles.models import Role, UserRole


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def seeded_roles(db):
    call_command("seed_roles")
    return {r.code: r for r in Role.objects.all()}


@pytest.fixture
def super_admin(db, seeded_roles):
    user = User.objects.create_superuser(
        mobile_number="9876543210",
        full_name="Super Admin User",
        password="StrongPassword@123",
    )
    UserRole.objects.create(user=user, role=seeded_roles["super_admin"])
    return user


@pytest.mark.django_db
class TestAuthentication:
    def test_mobile_login_sets_refresh_cookie_and_returns_access_token(self, api_client, super_admin):
        res = api_client.post(
            reverse("auth-login"),
            {"mobile_number": "+91 9876543210", "password": "StrongPassword@123"},
            format="json",
        )
        assert res.status_code == 200
        assert res.data["success"] is True
        assert "access" in res.data["data"]
        assert res.data["data"]["user"]["mobile_number"] == "9876543210"
        assert "hs_refresh_token" in res.cookies
        assert AuditLog.objects.filter(action="LOGIN_SUCCESS", user=super_admin).exists()

    def test_failed_login_lockout_protection(self, api_client, super_admin, settings):
        settings.AUTH_MAX_FAILED_LOGINS = 3
        for _ in range(3):
            res = api_client.post(
                reverse("auth-login"),
                {"mobile_number": "9876543210", "password": "WrongPassword!"},
                format="json",
            )
            assert res.status_code == 401

        # 4th attempt should return 423 Locked even with correct password
        locked_res = api_client.post(
            reverse("auth-login"),
            {"mobile_number": "9876543210", "password": "StrongPassword@123"},
            format="json",
        )
        assert locked_res.status_code == 423
        assert locked_res.data["error"]["code"] == "ACCOUNT_LOCKED"

    def test_token_refresh_and_logout_blacklist(self, api_client, super_admin):
        login_res = api_client.post(
            reverse("auth-login"),
            {"mobile_number": "9876543210", "password": "StrongPassword@123"},
            format="json",
        )
        access = login_res.data["data"]["access"]
        old_refresh = login_res.cookies["hs_refresh_token"].value

        refresh_res = api_client.post(reverse("auth-refresh"), {}, format="json")
        assert refresh_res.status_code == 200
        new_access = refresh_res.data["data"]["access"]

        # Old rotated refresh token must fail (blacklisted)
        replay_res = APIClient().post(reverse("auth-refresh"), {"refresh": old_refresh}, format="json")
        assert replay_res.status_code == 401

        # Logout blacklists current cookie refresh token
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {new_access}")
        logout_res = api_client.post(reverse("auth-logout"), {}, format="json")
        assert logout_res.status_code == 200

        # Refreshing after logout must fail
        after_logout_res = api_client.post(reverse("auth-refresh"), {}, format="json")
        assert after_logout_res.status_code == 401

    def test_change_password_and_relogin(self, api_client, super_admin):
        api_client.force_authenticate(user=super_admin)
        res = api_client.post(
            reverse("auth-change-password"),
            {
                "current_password": "StrongPassword@123",
                "new_password": "NewSecurePassword@456",
            },
            format="json",
        )
        assert res.status_code == 200

        api_client.force_authenticate(user=None)
        login_res = api_client.post(
            reverse("auth-login"),
            {"mobile_number": "9876543210", "password": "NewSecurePassword@456"},
            format="json",
        )
        assert login_res.status_code == 200

    def test_forgot_and_confirm_password_reset(self, api_client, super_admin, settings):
        settings.DEBUG = True
        forgot_res = api_client.post(
            reverse("auth-forgot-password"),
            {"mobile_number": "9876543210"},
            format="json",
        )
        assert forgot_res.status_code == 200
        uid = forgot_res.data["data"]["uid"]
        token = forgot_res.data["data"]["token"]

        reset_res = api_client.post(
            reverse("auth-reset-password"),
            {"uid": uid, "token": token, "new_password": "ResetPassword@789"},
            format="json",
        )
        assert reset_res.status_code == 200

        login_res = api_client.post(
            reverse("auth-login"),
            {"mobile_number": "9876543210", "password": "ResetPassword@789"},
            format="json",
        )
        assert login_res.status_code == 200


@pytest.mark.django_db
class TestUserManagement:
    def test_seed_roles_creates_five_initial_roles(self, seeded_roles):
        assert set(seeded_roles.keys()) == {
            "super_admin",
            "admin",
            "management",
            "rm",
            "mis_executive",
        }

    def test_admin_can_create_update_deactivate_and_block_self_deactivation(
        self, api_client, super_admin, seeded_roles
    ):
        api_client.force_authenticate(user=super_admin)

        create_res = api_client.post(
            reverse("users-list-create"),
            {
                "full_name": "Suresh RM",
                "mobile_number": "9123456789",
                "email": "suresh@havells.com",
                "password": "RmPassword@123",
                "reporting_manager": str(super_admin.id),
                "role_ids": [str(seeded_roles["rm"].id)],
            },
            format="json",
        )
        assert create_res.status_code == 201
        rm_id = create_res.data["data"]["id"]
        assert create_res.data["data"]["roles"][0]["code"] == "rm"

        # Self-deactivation must be blocked
        self_deact = api_client.post(reverse("users-deactivate", args=[super_admin.id]))
        assert self_deact.status_code == 403

        # Deactivating RM succeeds and blocks RM login
        deact_res = api_client.post(reverse("users-deactivate", args=[rm_id]))
        assert deact_res.status_code == 200
        assert deact_res.data["data"]["is_active"] is False

        api_client.force_authenticate(user=None)
        rm_login = api_client.post(
            reverse("auth-login"),
            {"mobile_number": "9123456789", "password": "RmPassword@123"},
            format="json",
        )
        assert rm_login.status_code == 403
        assert rm_login.data["error"]["code"] == "ACCOUNT_DEACTIVATED"

    def test_rm_cannot_access_user_management(self, api_client, seeded_roles):
        rm = User.objects.create_user(
            mobile_number="9111222333",
            full_name="Field RM",
            password="RmPassword@123",
        )
        UserRole.objects.create(user=rm, role=seeded_roles["rm"])
        api_client.force_authenticate(user=rm)

        res = api_client.get(reverse("users-list-create"))
        assert res.status_code == 403
