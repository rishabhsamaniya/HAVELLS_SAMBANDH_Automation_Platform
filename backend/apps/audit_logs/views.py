"""Read-only RBAC-protected views for inspecting immutable Audit Logs."""
from datetime import date

from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.audit_logs.selectors import get_audit_logs_queryset
from apps.audit_logs.serializers import AuditLogSerializer
from common.exceptions.domain import DomainError
from common.permissions.rbac import HasModulePermission
from common.responses.api import success_response


class AuditLogListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    required_permission = "audit_logs.view"
    serializer_class = AuditLogSerializer
    filterset_fields = ["module", "action", "object_type", "user"]
    search_fields = ["action", "object_id", "object_type", "user__full_name", "user__mobile_number"]
    ordering_fields = ["created_at", "module", "action"]

    def get_queryset(self):
        qs = get_audit_logs_queryset()
        start_raw = self.request.query_params.get("start_date")
        end_raw = self.request.query_params.get("end_date")
        try:
            if start_raw:
                qs = qs.filter(created_at__date__gte=date.fromisoformat(start_raw))
            if end_raw:
                qs = qs.filter(created_at__date__lte=date.fromisoformat(end_raw))
        except ValueError as exc:
            raise DomainError("Invalid date filter format. Expected YYYY-MM-DD.", code="INVALID_DATE") from exc
        return qs


class AuditLogDetailView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    required_permission = "audit_logs.view"

    def get(self, request, pk):
        entry = get_object_or_404(get_audit_logs_queryset(), pk=pk)
        return success_response(data=AuditLogSerializer(entry).data)
