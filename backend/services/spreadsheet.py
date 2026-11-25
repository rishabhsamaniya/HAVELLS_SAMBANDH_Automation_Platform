"""Shared Excel (.xlsx) and CSV generation utilities with formula-injection sanitization."""
import csv
import io
from typing import Iterable

from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def sanitize_cell_value(value):
    """Prevent CSV/Excel formula injection on user-controlled string cells."""
    if value is None:
        return ""
    if isinstance(value, str) and value and value[0] in FORMULA_PREFIXES:
        return f"'{value}"
    return value


def build_xlsx_response(
    *,
    filename: str,
    sheet_name: str,
    headers: list[str],
    rows: Iterable[list],
) -> HttpResponse:
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name[:31]

    header_fill = PatternFill(start_color="D71920", end_color="D71920", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")

    ws.append(headers)
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="left", vertical="center")

    for row in rows:
        ws.append([sanitize_cell_value(val) for val in row])

    # Auto-size columns reasonably
    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(max(max_len + 4, 14), 45)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def build_csv_response(
    *,
    filename: str,
    headers: list[str],
    rows: Iterable[list],
) -> HttpResponse:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([sanitize_cell_value(val) for val in row])

    response = HttpResponse(buffer.getvalue(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
