"""Business logic services for Dealer Management & Excel Import/Export."""
from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from openpyxl import load_workbook
from rest_framework import status

from apps.accounts.models import User
from apps.audit_logs.services import log_audit_event
from apps.campaigns.models import Campaign
from apps.dealers.models import Dealer, DealerStatus
from common.exceptions.domain import DomainError
from common.validators.mobile import (
    normalize_dealer_code,
    normalize_indian_mobile,
    validate_indian_mobile,
)

COLUMN_ALIASES = {
    "dealer_code": {"dealer_code", "code", "dealercode", "dealer_id"},
    "mobile_number": {"mobile_number", "mobile", "dealer_mobile", "dealer_mobile_number", "phone", "phone_number"},
    "assigned_rm_mobile": {"assigned_rm_mobile", "rm_mobile", "rm_mobile_number", "rm_phone"},
    "campaign_code": {"campaign_code", "campaign", "campaign_name"},
    "status": {"status"},
}
REQUIRED_IMPORT_COLUMNS = {"dealer_code", "mobile_number", "assigned_rm_mobile"}


def _normalize_header(raw) -> str:
    return "_".join(str(raw or "").strip().lower().replace("-", " ").split())


def _resolve_column_indices(header_row) -> tuple[dict[str, int], set[str]]:
    col_idx: dict[str, int] = {}
    for idx, raw_header in enumerate(header_row):
        norm = _normalize_header(raw_header)
        if not norm:
            continue
        for canonical, aliases in COLUMN_ALIASES.items():
            if norm in aliases and canonical not in col_idx:
                col_idx[canonical] = idx
    missing = REQUIRED_IMPORT_COLUMNS - set(col_idx.keys())
    return col_idx, missing


@transaction.atomic
def create_dealer(
    *,
    actor: User,
    dealer_code: str,
    mobile_number: str,
    assigned_rm: User,
    campaign: Campaign | None = None,
    dealer_status: str = DealerStatus.ACTIVE,
) -> Dealer:
    dealer = Dealer.objects.create(
        dealer_code=normalize_dealer_code(dealer_code),
        mobile_number=normalize_indian_mobile(mobile_number),
        assigned_rm=assigned_rm,
        campaign=campaign,
        status=dealer_status,
        created_by=actor,
    )
    log_audit_event(
        user=actor,
        action="DEALER_CREATED",
        module="dealers",
        object_type="Dealer",
        object_id=str(dealer.id),
        new_values={
            "dealer_code": dealer.dealer_code,
            "mobile_number": dealer.mobile_number,
            "assigned_rm_id": str(dealer.assigned_rm_id),
            "campaign_id": str(dealer.campaign_id) if dealer.campaign_id else None,
            "status": dealer.status,
        },
    )
    return dealer


@transaction.atomic
def update_dealer(*, actor: User, dealer: Dealer, validated_data: dict) -> Dealer:
    old_values = {
        "dealer_code": dealer.dealer_code,
        "mobile_number": dealer.mobile_number,
        "assigned_rm_id": str(dealer.assigned_rm_id),
        "status": dealer.status,
    }
    for field, value in validated_data.items():
        setattr(dealer, field, value)
    dealer.save()

    log_audit_event(
        user=actor,
        action="DEALER_UPDATED",
        module="dealers",
        object_type="Dealer",
        object_id=str(dealer.id),
        old_values=old_values,
        new_values={
            "dealer_code": dealer.dealer_code,
            "mobile_number": dealer.mobile_number,
            "assigned_rm_id": str(dealer.assigned_rm_id),
            "status": dealer.status,
        },
    )
    return dealer


@transaction.atomic
def deactivate_dealer(*, actor: User, dealer: Dealer) -> Dealer:
    old_status = dealer.status
    dealer.status = DealerStatus.INACTIVE
    dealer.save(update_fields=["status", "updated_at"])

    log_audit_event(
        user=actor,
        action="DEALER_DEACTIVATED",
        module="dealers",
        object_type="Dealer",
        object_id=str(dealer.id),
        old_values={"status": old_status},
        new_values={"status": dealer.status},
    )
    return dealer


def import_dealers_from_excel(
    *,
    actor: User,
    uploaded_file,
    default_campaign: Campaign | None = None,
) -> dict:
    """
    Validate and import dealers from an .xlsx file.
    - Rejects non-.xlsx files and files exceeding MAX_EXCEL_UPLOAD_MB.
    - Validates required columns: dealer_code, mobile_number, assigned_rm_mobile.
    - Rejects duplicate dealer codes (in DB or within the file); NEVER silently overwrites.
    - Returns row-level errors and an import summary.
    """
    filename = getattr(uploaded_file, "name", "") or ""
    if not filename.lower().endswith(".xlsx"):
        raise DomainError(
            message="Invalid file type. Please upload an Excel (.xlsx) file.",
            code="INVALID_FILE_TYPE",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    max_bytes = getattr(settings, "MAX_EXCEL_UPLOAD_MB", 5) * 1024 * 1024
    if getattr(uploaded_file, "size", 0) > max_bytes:
        raise DomainError(
            message=f"File size exceeds the maximum allowed limit of {getattr(settings, 'MAX_EXCEL_UPLOAD_MB', 5)} MB.",
            code="FILE_TOO_LARGE",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Verify OOXML (.xlsx) ZIP magic header bytes to block disguised non-Excel uploads
    magic_bytes = uploaded_file.read(4)
    uploaded_file.seek(0)
    if magic_bytes != b"PK\x03\x04":
        raise DomainError(
            message="Invalid Excel file signature. Please upload a genuine .xlsx workbook.",
            code="INVALID_FILE_TYPE",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        wb = load_workbook(uploaded_file, read_only=True, data_only=True)
        ws = wb.active
        rows_iter = ws.iter_rows(values_only=True)
        header_row = next(rows_iter, None)
    except Exception as exc:
        raise DomainError(
            message="Unable to read the uploaded Excel file. Ensure it is a valid .xlsx workbook.",
            code="CORRUPT_EXCEL_FILE",
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc

    if not header_row:
        raise DomainError(
            message="Uploaded Excel file is empty.",
            code="EMPTY_FILE",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    col_idx, missing_cols = _resolve_column_indices(header_row)
    if missing_cols:
        raise DomainError(
            message=(
                f"Missing required column(s): {', '.join(sorted(missing_cols))}. "
                f"Expected headers: dealer_code, mobile_number, assigned_rm_mobile (optional: status)."
            ),
            code="MISSING_REQUIRED_COLUMNS",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"missing_columns": sorted(missing_cols)},
        )

    existing_codes = set(Dealer.objects.values_list("dealer_code", flat=True))
    active_users_by_mobile = {
        u.mobile_number: u for u in User.objects.filter(is_active=True)
    }
    campaigns_by_key: dict[str, Campaign] = {}
    for c in Campaign.objects.all():
        campaigns_by_key[c.campaign_code.strip().upper()] = c
        campaigns_by_key[c.campaign_name.strip().upper()] = c

    seen_codes_in_file: set[str] = set()
    to_create: list[Dealer] = []
    row_errors: list[dict] = []
    total_rows = 0

    for row_num, raw_row in enumerate(rows_iter, start=2):
        # Skip completely blank rows
        if not raw_row or all(cell is None or str(cell).strip() == "" for cell in raw_row):
            continue

        total_rows += 1
        errors_for_row: list[str] = []

        raw_code = raw_row[col_idx["dealer_code"]] if col_idx["dealer_code"] < len(raw_row) else ""
        raw_mobile = raw_row[col_idx["mobile_number"]] if col_idx["mobile_number"] < len(raw_row) else ""
        raw_rm_mobile = (
            raw_row[col_idx["assigned_rm_mobile"]]
            if col_idx["assigned_rm_mobile"] < len(raw_row)
            else ""
        )
        raw_campaign = (
            raw_row[col_idx["campaign_code"]]
            if "campaign_code" in col_idx and col_idx["campaign_code"] < len(raw_row)
            else ""
        )
        raw_status = (
            raw_row[col_idx["status"]]
            if "status" in col_idx and col_idx["status"] < len(raw_row)
            else DealerStatus.ACTIVE
        )

        dealer_code = normalize_dealer_code(raw_code)
        if not dealer_code:
            errors_for_row.append("dealer_code is required.")
        elif dealer_code in existing_codes:
            errors_for_row.append(f"Dealer code '{dealer_code}' already exists (existing records are not overwritten).")
        elif dealer_code in seen_codes_in_file:
            errors_for_row.append(f"Duplicate dealer_code '{dealer_code}' within uploaded file.")

        mobile_str = normalize_indian_mobile(str(raw_mobile or "").split(".")[0])
        try:
            validate_indian_mobile(mobile_str)
        except DjangoValidationError:
            errors_for_row.append("Invalid 10-digit Indian mobile number.")

        rm_mobile_str = normalize_indian_mobile(str(raw_rm_mobile or "").split(".")[0])
        rm_user = active_users_by_mobile.get(rm_mobile_str)
        if not rm_user:
            errors_for_row.append(f"Assigned RM with mobile '{rm_mobile_str or raw_rm_mobile}' not found or inactive.")

        resolved_campaign = default_campaign
        campaign_key = str(raw_campaign or "").strip().upper()
        if campaign_key:
            resolved_campaign = campaigns_by_key.get(campaign_key)
            if not resolved_campaign:
                errors_for_row.append(f"Campaign '{raw_campaign}' not found.")

        dealer_status = str(raw_status or DealerStatus.ACTIVE).strip().lower()
        if dealer_status not in (DealerStatus.ACTIVE, DealerStatus.INACTIVE):
            errors_for_row.append(f"Invalid status '{dealer_status}'. Allowed: active, inactive.")

        if errors_for_row:
            row_errors.append(
                {
                    "row_number": row_num,
                    "dealer_code": dealer_code,
                    "errors": errors_for_row,
                }
            )
            continue

        seen_codes_in_file.add(dealer_code)
        to_create.append(
            Dealer(
                dealer_code=dealer_code,
                mobile_number=mobile_str,
                assigned_rm=rm_user,
                campaign=resolved_campaign,
                status=dealer_status,
                created_by=actor,
            )
        )

    with transaction.atomic():
        if to_create:
            Dealer.objects.bulk_create(to_create)

    summary = {
        "total_rows": total_rows,
        "created_count": len(to_create),
        "failed_count": len(row_errors),
        "errors": row_errors,
    }

    log_audit_event(
        user=actor,
        action="DEALERS_IMPORTED",
        module="dealers",
        object_type="Dealer",
        new_values={
            "filename": filename,
            "total_rows": total_rows,
            "created_count": len(to_create),
            "failed_count": len(row_errors),
        },
    )
    return summary
