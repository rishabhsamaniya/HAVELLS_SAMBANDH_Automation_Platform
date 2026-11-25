"""Automated tests for Phase 07: Dealer CRUD, RM Isolation, Excel Import & Export."""
import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.urls import reverse
from openpyxl import Workbook
import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.audit_logs.models import AuditLog
from apps.dealers.models import Dealer
from apps.roles.models import Role, UserRole


@pytest.fixture
def rbac_users(db):
    call_command("seed_rbac")
    roles = {r.code: r for r in Role.objects.all()}

    admin = User.objects.create_user("9800000001", "Admin One", "AdminPass@123")
    UserRole.objects.create(user=admin, role=roles["admin"])

    rm1 = User.objects.create_user("9800000002", "RM One", "RmPass@123")
    UserRole.objects.create(user=rm1, role=roles["rm"])

    rm2 = User.objects.create_user("9800000003", "RM Two", "RmPass@123")
    UserRole.objects.create(user=rm2, role=roles["rm"])

    mis = User.objects.create_user("9800000004", "MIS Exec", "MisPass@123")
    UserRole.objects.create(user=mis, role=roles["mis_executive"])

    return {"admin": admin, "rm1": rm1, "rm2": rm2, "mis": mis}


def _make_xlsx_file(headers, rows, filename="dealers.xlsx"):
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return SimpleUploadedFile(
        filename,
        buf.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@pytest.mark.django_db
class TestDealerManagement:
    def test_admin_create_update_deactivate_and_duplicate_code_rejected(self, rbac_users):
        client = APIClient()
        client.force_authenticate(user=rbac_users["admin"])

        res = client.post(
            reverse("dealers-list-create"),
            {
                "dealer_code": " hvl-1001 ",
                "mobile_number": "+91 9811111111",
                "assigned_rm": str(rbac_users["rm1"].id),
            },
            format="json",
        )
        assert res.status_code == 201
        dealer_id = res.data["data"]["id"]
        assert res.data["data"]["dealer_code"] == "HVL-1001"
        assert res.data["data"]["mobile_number"] == "9811111111"

        # Duplicate dealer_code rejected
        dup_res = client.post(
            reverse("dealers-list-create"),
            {
                "dealer_code": "HVL-1001",
                "mobile_number": "9822222222",
                "assigned_rm": str(rbac_users["rm1"].id),
            },
            format="json",
        )
        assert dup_res.status_code == 400

        # Deactivate dealer
        deact_res = client.post(reverse("dealers-deactivate", args=[dealer_id]))
        assert deact_res.status_code == 200
        assert deact_res.data["data"]["status"] == "inactive"

    def test_rm_strict_data_isolation_on_list_detail_and_export(self, rbac_users):
        d1 = Dealer.objects.create(dealer_code="D-RM1", mobile_number="9111111111", assigned_rm=rbac_users["rm1"])
        d2 = Dealer.objects.create(dealer_code="D-RM2", mobile_number="9222222222", assigned_rm=rbac_users["rm2"])

        client = APIClient()
        client.force_authenticate(user=rbac_users["rm1"])

        list_res = client.get(reverse("dealers-list-create"))
        assert list_res.status_code == 200
        codes = [item["dealer_code"] for item in list_res.data["data"]]
        assert codes == ["D-RM1"]

        # Cannot access RM2's dealer
        assert client.get(reverse("dealers-detail-update", args=[d2.id])).status_code == 404
        # Can access own dealer
        assert client.get(reverse("dealers-detail-update", args=[d1.id])).status_code == 200

        # CSV export only includes RM1's dealer
        csv_res = client.get(reverse("dealers-export") + "?format=csv")
        assert csv_res.status_code == 200
        body = csv_res.content.decode("utf-8")
        assert "D-RM1" in body
        assert "D-RM2" not in body

    def test_excel_import_validates_rows_and_never_overwrites_existing(self, rbac_users):
        Dealer.objects.create(
            dealer_code="EXIST-01",
            mobile_number="9999999999",
            assigned_rm=rbac_users["rm1"],
        )

        xlsx = _make_xlsx_file(
            ["dealer_code", "mobile_number", "assigned_rm_mobile", "status"],
            [
                ["NEW-01", "9876543211", "9800000002", "active"],  # Valid
                ["EXIST-01", "9876543212", "9800000002", "active"],  # Existing DB duplicate -> reject
                ["NEW-01", "9876543213", "9800000002", "active"],  # Duplicate in file -> reject
                ["BAD-MOB", "12345", "9800000002", "active"],  # Invalid mobile -> reject
                ["BAD-RM", "9876543214", "9999900000", "active"],  # Nonexistent RM -> reject
            ],
        )

        client = APIClient()
        client.force_authenticate(user=rbac_users["mis"])
        res = client.post(reverse("dealers-import"), {"file": xlsx}, format="multipart")
        assert res.status_code == 200
        summary = res.data["data"]
        assert summary["total_rows"] == 5
        assert summary["created_count"] == 1
        assert summary["failed_count"] == 4
        assert len(summary["errors"]) == 4

        # Existing record was NOT overwritten
        existing = Dealer.objects.get(dealer_code="EXIST-01")
        assert existing.mobile_number == "9999999999"
        assert Dealer.objects.filter(dealer_code="NEW-01").exists()
        assert AuditLog.objects.filter(action="DEALERS_IMPORTED", user=rbac_users["mis"]).exists()

    def test_excel_import_rejects_invalid_file_type_and_rm_forbidden(self, rbac_users):
        client = APIClient()
        # RM does not have dealers.import permission
        client.force_authenticate(user=rbac_users["rm1"])
        csv_file = SimpleUploadedFile("bad.csv", b"a,b,c", content_type="text/csv")
        assert client.post(reverse("dealers-import"), {"file": csv_file}, format="multipart").status_code == 403

        # MIS with wrong file type gets 400
        client.force_authenticate(user=rbac_users["mis"])
        res = client.post(reverse("dealers-import"), {"file": csv_file}, format="multipart")
        assert res.status_code == 400
        assert res.data["error"]["code"] == "INVALID_FILE_TYPE"

    def test_excel_import_accepts_human_friendly_headers_and_template_download_works(self, rbac_users):
        client = APIClient()
        client.force_authenticate(user=rbac_users["mis"])

        # Download template works
        tpl = client.get(reverse("dealers-import-template"))
        assert tpl.status_code == 200
        assert "spreadsheetml" in tpl["Content-Type"]

        # Human-readable headers like exported sheet ("Dealer Code", "Mobile Number", "RM Mobile") work
        xlsx = _make_xlsx_file(
            ["Dealer Code", "Mobile Number", "RM Mobile", "Status"],
            [["FRIENDLY-01", "9876543299", "9800000002", "active"]],
        )
        res = client.post(reverse("dealers-import"), {"file": xlsx}, format="multipart")
        assert res.status_code == 200
        assert res.data["data"]["created_count"] == 1
        assert Dealer.objects.filter(dealer_code="FRIENDLY-01").exists()
