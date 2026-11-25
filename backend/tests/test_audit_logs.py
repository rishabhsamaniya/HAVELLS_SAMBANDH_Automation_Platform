"""Automated tests for Phase 14: Audit Log API, Immutability, RBAC & Secret Redaction."""
from django.core.management import call_command
from django.urls import reverse
import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.audit_logs.services import log_audit_event
from apps.roles.models import Role, UserRole


@pytest.mark.django_db
class TestAuditLogging:
    def test_audit_log_redacts_sensitive_credentials_and_tokens(self):
        entry = log_audit_event(
            user=None,
            action="TEST_SENSITIVE_EVENT",
            module="accounts",
            object_type="User",
            object_id="123",
            new_values={
                "mobile_number": "9876543210",
                "password": "PlainTextSecret!123",
                "nested": {"token": "raw-secret-token", "refresh": "jwt-refresh"},
            },
        )
        assert entry.new_values["mobile_number"] == "9876543210"
        assert entry.new_values["password"] == "[REDACTED]"
        assert entry.new_values["nested"]["token"] == "[REDACTED]"
        assert entry.new_values["nested"]["refresh"] == "[REDACTED]"

    def test_audit_logs_api_rbac_and_immutability(self):
        call_command("seed_rbac")
        roles = {r.code: r for r in Role.objects.all()}

        admin = User.objects.create_user("9800070001", "Audit Admin", "AdminPass@123")
        UserRole.objects.create(user=admin, role=roles["admin"])

        rm = User.objects.create_user("9800070002", "Audit RM", "RmPass@123")
        UserRole.objects.create(user=rm, role=roles["rm"])

        entry = log_audit_event(
            user=admin,
            action="DEALER_CREATED",
            module="dealers",
            object_type="Dealer",
            object_id="dlr-1",
            new_values={"dealer_code": "D1"},
        )

        # RM cannot view audit logs -> 403
        rm_client = APIClient()
        rm_client.force_authenticate(user=rm)
        assert rm_client.get(reverse("audit-logs-list")).status_code == 403

        # Admin can list, filter, and inspect detail
        admin_client = APIClient()
        admin_client.force_authenticate(user=admin)
        list_res = admin_client.get(reverse("audit-logs-list") + "?module=dealers")
        assert list_res.status_code == 200
        assert len(list_res.data["data"]) >= 1

        detail_res = admin_client.get(reverse("audit-logs-detail", args=[entry.id]))
        assert detail_res.status_code == 200
        assert detail_res.data["data"]["action"] == "DEALER_CREATED"

        # Immutability: DELETE / PATCH not permitted
        assert admin_client.delete(reverse("audit-logs-detail", args=[entry.id])).status_code == 405
        assert admin_client.patch(reverse("audit-logs-detail", args=[entry.id]), {}).status_code == 405
