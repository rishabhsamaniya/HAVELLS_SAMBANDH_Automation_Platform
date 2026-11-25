"""Views for the 8 standard Havells Sambandh reports and Excel/CSV export."""
from datetime import date

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.audit_logs.services import log_audit_event
from apps.reports.selectors import REPORT_REGISTRY
from common.exceptions.domain import DomainError
from common.permissions.rbac import HasModulePermission
from common.responses.api import success_response
from services.spreadsheet import build_csv_response, build_xlsx_response


def _extract_filters(request) -> dict:
    filters = {
        "campaign": request.query_params.get("campaign") or None,
        "assigned_rm": request.query_params.get("assigned_rm") or None,
        "dealer_code": request.query_params.get("dealer_code") or None,
        "status": request.query_params.get("status") or None,
    }
    for key in ("start_date", "end_date"):
        raw = request.query_params.get(key)
        if raw:
            try:
                filters[key] = date.fromisoformat(raw)
            except ValueError as exc:
                raise DomainError(f"Invalid '{key}' format. Expected YYYY-MM-DD.", code="INVALID_DATE") from exc
    return filters


class BaseReportView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    required_permission = "reports.view"
    report_key: str = ""

    def get(self, request):
        title, builder = REPORT_REGISTRY[self.report_key]
        headers, rows = builder(request.user, _extract_filters(request))
        return success_response(
            data={
                "report": self.report_key,
                "title": title,
                "headers": headers,
                "total": len(rows),
                "rows": rows,
            }
        )


class DealerMasterReportView(BaseReportView):
    report_key = "dealer_master"


class ConfirmationReportView(BaseReportView):
    report_key = "confirmations"


class PendingDealerReportView(BaseReportView):
    report_key = "pending"


class RMPerformanceReportView(BaseReportView):
    report_key = "rm_performance"


class CampaignWiseReportView(BaseReportView):
    report_key = "campaign_wise"


class DateWiseReportView(BaseReportView):
    report_key = "date_wise"


class TimeSlotReportView(BaseReportView):
    report_key = "time_slot"


class LinkUsageReportView(BaseReportView):
    report_key = "link_usage"


class ReportExportView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    required_permission = "reports.export"

    def get(self, request):
        report_key = (request.query_params.get("report") or "confirmations").strip().lower()
        if report_key not in REPORT_REGISTRY:
            raise DomainError(
                message=f"Unknown report '{report_key}'. Allowed: {', '.join(REPORT_REGISTRY.keys())}.",
                code="INVALID_REPORT_TYPE",
            )

        export_format = (request.query_params.get("format") or "xlsx").strip().lower()
        title, builder = REPORT_REGISTRY[report_key]
        headers, dict_rows = builder(request.user, _extract_filters(request))
        matrix_rows = [[row.get(h, "") for h in headers] for row in dict_rows]

        log_audit_event(
            user=request.user,
            action="REPORT_EXPORTED",
            module="reports",
            object_type="Report",
            object_id=report_key,
            new_values={"format": export_format, "record_count": len(matrix_rows)},
        )

        if export_format == "csv":
            return build_csv_response(
                filename=f"havells_{report_key}_report.csv",
                headers=headers,
                rows=matrix_rows,
            )
        return build_xlsx_response(
            filename=f"havells_{report_key}_report.xlsx",
            sheet_name=title,
            headers=headers,
            rows=matrix_rows,
        )
