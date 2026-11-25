"""Automated tests for Phase 06: Dynamic RBAC, PermissionService & RM Data Isolation."""
from django.core.management import call_command
from django.urls import reverse
import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.audit_logs.models import AuditLog
from apps.dealers.models import Dealer
from apps.permissions.models import Permission
from apps.permissions.services import PermissionService
from apps.roles.models import Role, UserRole


@pytest.fixture
def seeded_rbac(db):
    call_command("seed_rbac")
    return {r.code: r for r in Role.objects.all()}


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestDynamicRBAC:
    def test_seed_rbac_populates_roles_and_permissions(self, seeded_rbac):
        assert len(seeded_rbac) == 5
        assert Permission.objects.count() >= 30
        assert seeded_rbac["management"].role_permissions.filter(
            permission__codename="dashboard.view"
        ).exists()
        assert not seeded_rbac["management"].role_permissions.filter(
            permission__codename="users.add"
        ).exists()

    def test_super_admin_creates_role_and_dynamically_assigns_permissions(
        self, api_client, seeded_rbac
    ):
        sa = User.objects.create_superuser("9876500001", "SA One", "SuperPass@123")
        UserRole.objects.create(user=sa, role=seeded_rbac["super_admin"])
        api_client.force_authenticate(user=sa)

        # Create custom role
        res = api_client.post(
            reverse("roles-list-create"),
            {
                "name": "Regional Coordinator",
                "code": "regional_coordinator",
                "description": "Coordinates regional confirmations",
            },
            format="json",
        )
        assert res.status_code == 201
        role_id = res.data["data"]["id"]

        # Assign users.view dynamically to custom role
        users_view_perm = Permission.objects.get(codename="users.view")
        assign_res = api_client.post(
            reverse("roles-permissions", args=[role_id]),
            {"permission_ids": [str(users_view_perm.id)]},
            format="json",
        )
        assert assign_res.status_code == 200
        assert assign_res.data["data"]["permissions_count"] == 1
        assert AuditLog.objects.filter(action="ROLE_PERMISSIONS_UPDATED", object_id=role_id).exists()

        # Assign custom role to a regular user and verify backend enforces it immediately
        coord = User.objects.create_user("9876500002", "Coord User", "CoordPass@123")
        UserRole.objects.create(user=coord, role_id=role_id)

        api_client.force_authenticate(user=coord)
        assert api_client.get(reverse("users-list-create")).status_code == 200
        # Does NOT have users.add -> 403
        create_attempt = api_client.post(
            reverse("users-list-create"),
            {"full_name": "X", "mobile_number": "9876500099", "password": "Password@123"},
            format="json",
        )
        assert create_attempt.status_code == 403

    def test_super_admin_system_role_cannot_be_deactivated(self, api_client, seeded_rbac):
        sa = User.objects.create_superuser("9876500003", "SA Two", "SuperPass@123")
        api_client.force_authenticate(user=sa)
        res = api_client.patch(
            reverse("roles-detail-update", args=[seeded_rbac["super_admin"].id]),
            {"is_active": False},
            format="json",
        )
        assert res.status_code == 403
        assert res.data["error"]["code"] == "SYSTEM_ROLE_PROTECTED"

    def test_rm_queryset_isolation_enforced_by_permission_service(self, seeded_rbac):
        rm1 = User.objects.create_user("9876500010", "RM One", "RmPass@123")
        rm2 = User.objects.create_user("9876500011", "RM Two", "RmPass@123")
        admin = User.objects.create_user("9876500012", "Admin One", "AdminPass@123")
        UserRole.objects.create(user=rm1, role=seeded_rbac["rm"])
        UserRole.objects.create(user=rm2, role=seeded_rbac["rm"])
        UserRole.objects.create(user=admin, role=seeded_rbac["admin"])

        d1 = Dealer.objects.create(dealer_code="DLR001", mobile_number="9000000001", assigned_rm=rm1)
        d2 = Dealer.objects.create(dealer_code="DLR002", mobile_number="9000000002", assigned_rm=rm2)

        rm1_dealers = list(PermissionService.scope_dealer_queryset(rm1, Dealer.objects.all()))
        assert rm1_dealers == [d1]
        assert d2 not in rm1_dealers

        admin_dealers = set(PermissionService.scope_dealer_queryset(admin, Dealer.objects.all()))
        assert admin_dealers == {d1, d2}

    def test_non_privileged_user_cannot_list_or_manage_roles(self, api_client, seeded_rbac):
        rm = User.objects.create_user("9876500020", "RM Three", "RmPass@123")
        UserRole.objects.create(user=rm, role=seeded_rbac["rm"])
        api_client.force_authenticate(user=rm)

        assert api_client.get(reverse("roles-list-create")).status_code == 403
        assert api_client.get(reverse("permissions-list")).status_code == 403
