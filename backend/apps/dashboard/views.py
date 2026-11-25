"""Views for Admin Dashboard Overview & Analytics."""
from datetime import date

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.dashboard.selectors import get_dashboard_analytics, get_dashboard_overview
from common.exceptions.domain import DomainError
from common.permissions.rbac import HasModulePermission
from common.responses.api import success_response


def _parse_optional_date(raw: str | None, param_name: str) -> date | None:
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise DomainError(f"Invalid '{param_name}' format. Expected YYYY-MM-DD.", code="INVALID_DATE") from exc


class DashboardOverviewView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    required_permission = "dashboard.view"

    def get(self, request):
        campaign_id = request.query_params.get("campaign") or None
        start_date = _parse_optional_date(request.query_params.get("start_date"), "start_date")
        end_date = _parse_optional_date(request.query_params.get("end_date"), "end_date")
        data = get_dashboard_overview(
            user=request.user,
            campaign_id=campaign_id,
            start_date=start_date,
            end_date=end_date,
        )
        return success_response(data=data)


class DashboardAnalyticsView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    required_permission = "dashboard.view"

    def get(self, request):
        campaign_id = request.query_params.get("campaign") or None
        start_date = _parse_optional_date(request.query_params.get("start_date"), "start_date")
        end_date = _parse_optional_date(request.query_params.get("end_date"), "end_date")
        data = get_dashboard_analytics(
            user=request.user,
            campaign_id=campaign_id,
            start_date=start_date,
            end_date=end_date,
        )
        return success_response(data=data)
