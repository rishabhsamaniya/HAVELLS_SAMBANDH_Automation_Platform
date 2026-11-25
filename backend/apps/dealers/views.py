"""Views for Dealer Management, Excel Import, Excel/CSV Export, and Confirmation History."""
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.audit_logs.services import log_audit_event
from apps.dealers.selectors import (
    get_dealer_confirmation_history,
    get_scoped_dealers_queryset,
)
from apps.dealers.serializers import (
    DealerCreateSerializer,
    DealerSerializer,
    DealerUpdateSerializer,
)
from apps.dealers.services import (
    create_dealer,
    deactivate_dealer,
    import_dealers_from_excel,
    update_dealer,
)
from common.exceptions.domain import DomainError
from common.permissions.rbac import HasModulePermission
from common.responses.api import success_response
from services.spreadsheet import build_csv_response, build_xlsx_response


class DealerListCreateView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    method_permissions = {
        "GET": "dealers.view",
        "POST": "dealers.add",
    }
    serializer_class = DealerSerializer
    search_fields = ["dealer_code", "mobile_number"]
    filterset_fields = ["dealer_code", "assigned_rm", "status"]
    ordering_fields = ["created_at", "dealer_code", "status"]

    def get_queryset(self):
        return get_scoped_dealers_queryset(self.request.user)

    def post(self, request):
        serializer = DealerCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dealer = create_dealer(
            actor=request.user,
            dealer_code=serializer.validated_data["dealer_code"],
            mobile_number=serializer.validated_data["mobile_number"],
            assigned_rm=serializer.validated_data["assigned_rm"],
            dealer_status=serializer.validated_data["status"],
        )
        return success_response(
            data=DealerSerializer(dealer).data,
            message="Dealer created successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class DealerDetailUpdateView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    method_permissions = {
        "GET": "dealers.view",
        "PATCH": "dealers.edit",
    }

    def get(self, request, pk):
        dealer = get_object_or_404(get_scoped_dealers_queryset(request.user), pk=pk)
        return success_response(data=DealerSerializer(dealer).data)

    def patch(self, request, pk):
        dealer = get_object_or_404(get_scoped_dealers_queryset(request.user), pk=pk)
        serializer = DealerUpdateSerializer(
            data=request.data,
            partial=True,
            context={"dealer": dealer},
        )
        serializer.is_valid(raise_exception=True)
        updated = update_dealer(
            actor=request.user,
            dealer=dealer,
            validated_data=serializer.validated_data,
        )
        return success_response(
            data=DealerSerializer(updated).data,
            message="Dealer updated successfully.",
        )


class DealerDeactivateView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    required_permission = "dealers.delete"

    def post(self, request, pk):
        dealer = get_object_or_404(get_scoped_dealers_queryset(request.user), pk=pk)
        updated = deactivate_dealer(actor=request.user, dealer=dealer)
        return success_response(
            data=DealerSerializer(updated).data,
            message="Dealer deactivated successfully.",
        )


class DealerConfirmationHistoryView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    required_permission = "dealers.view"

    def get(self, request, pk):
        dealer = get_object_or_404(get_scoped_dealers_queryset(request.user), pk=pk)
        confirmations = get_dealer_confirmation_history(dealer)
        data = [
            {
                "id": str(c.id),
                "campaign_name": c.campaign.campaign_name,
                "preferred_date": c.preferred_date,
                "preferred_time_slot": c.preferred_time_slot.display_label,
                "submission_status": c.submission_status,
                "submitted_at": c.submitted_at,
            }
            for c in confirmations
        ]
        return success_response(data=data)


class DealerImportExcelView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    required_permission = "dealers.import"
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            raise DomainError(
                message="Please attach an Excel (.xlsx) file under the 'file' field.",
                code="FILE_REQUIRED",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        summary = import_dealers_from_excel(actor=request.user, uploaded_file=uploaded_file)
        return success_response(
            data=summary,
            message=f"Import completed: {summary['created_count']} created, {summary['failed_count']} failed.",
        )


class DealerImportTemplateView(APIView):
    """Download a pre-formatted .xlsx template for Dealer Excel imports."""

    permission_classes = [IsAuthenticated, HasModulePermission]
    required_permission = "dealers.import"

    def get(self, request):
        sample_rm_mobile = request.user.mobile_number or "9876543210"
        return build_xlsx_response(
            filename="havells_dealers_import_template.xlsx",
            sheet_name="Dealers Template",
            headers=["dealer_code", "mobile_number", "assigned_rm_mobile", "status"],
            rows=[
                ["HVL-1001", "9876543210", sample_rm_mobile, "active"],
            ],
        )


class DealerExportView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    required_permission = "dealers.export"

    def get(self, request):
        qs = get_scoped_dealers_queryset(request.user)

        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        rm_filter = request.query_params.get("assigned_rm")
        if rm_filter:
            qs = qs.filter(assigned_rm_id=rm_filter)
        dealer_code = request.query_params.get("dealer_code")
        if dealer_code:
            qs = qs.filter(dealer_code__icontains=dealer_code.strip())

        export_format = (request.query_params.get("format") or "xlsx").lower()
        headers = [
            "Dealer Code",
            "Mobile Number",
            "Status",
            "Assigned RM",
            "RM Mobile",
            "Created At",
        ]
        rows = [
            [
                d.dealer_code,
                d.mobile_number,
                d.status,
                d.assigned_rm.full_name,
                d.assigned_rm.mobile_number,
                d.created_at.strftime("%Y-%m-%d %H:%M"),
            ]
            for d in qs
        ]

        log_audit_event(
            user=request.user,
            action="DEALERS_EXPORTED",
            module="dealers",
            object_type="Dealer",
            new_values={"format": export_format, "record_count": len(rows)},
        )

        if export_format == "csv":
            return build_csv_response(filename="havells_dealers.csv", headers=headers, rows=rows)
        return build_xlsx_response(
            filename="havells_dealers.xlsx",
            sheet_name="Dealers",
            headers=headers,
            rows=rows,
        )
