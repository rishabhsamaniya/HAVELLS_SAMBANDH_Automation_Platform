"""Automated tests for Phase 16: Security Headers, Upload Hardening, Formula Sanitization & Safe Errors."""
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.urls import reverse
import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.roles.models import Role, UserRole
from common.exceptions.handler import custom_exception_handler
from services.spreadsheet import sanitize_cell_value


@pytest.mark.django_db
class TestSecurityHardening:
    def test_security_headers_and_no_store_on_sensitive_endpoints(self):
        client = APIClient()
        res = client.get(reverse("health-check"))
        assert res["X-Content-Type-Options"] == "nosniff"
        assert res["X-Frame-Options"] == "DENY"
        assert res["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert "Permissions-Policy" in res

        pub = client.get(reverse("public-confirm-detail", args=["invalid-token"]))
        assert "no-store" in pub["Cache-Control"]

    def test_disguised_non_zip_xlsx_upload_is_rejected_by_magic_bytes(self):
        call_command("seed_rbac")
        roles = {r.code: r for r in Role.objects.all()}
        admin = User.objects.create_user("9800080001", "Sec Admin", "AdminPass@123")
        UserRole.objects.create(user=admin, role=roles["admin"])

        fake_xlsx = SimpleUploadedFile(
            "malicious.xlsx",
            b"<script>alert(1)</script>",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        client = APIClient()
        client.force_authenticate(user=admin)
        res = client.post(reverse("dealers-import"), {"file": fake_xlsx}, format="multipart")
        assert res.status_code == 400
        assert res.data["error"]["code"] == "INVALID_FILE_TYPE"

    def test_spreadsheet_formula_injection_neutralized(self):
        assert sanitize_cell_value("=CMD|' /C calc'!A0").startswith("'")
        assert sanitize_cell_value("+SUM(A1:A2)").startswith("'")
        assert sanitize_cell_value("-1+1").startswith("'")
        assert sanitize_cell_value("@SUM(1,2)").startswith("'")
        assert sanitize_cell_value("HVL-1001") == "HVL-1001"

    def test_unhandled_exception_hides_internal_stack_trace(self):
        resp = custom_exception_handler(RuntimeError("Sensitive DB detail"), {})
        assert resp.status_code == 500
        assert resp.data["success"] is False
        assert resp.data["error"]["code"] == "INTERNAL_SERVER_ERROR"
        assert "Sensitive DB detail" not in str(resp.data)
