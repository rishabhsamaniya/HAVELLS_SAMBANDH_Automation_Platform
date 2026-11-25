"""Reusable read queries for immutable AuditLog records."""
from django.db.models import QuerySet

from apps.audit_logs.models import AuditLog


def get_audit_logs_queryset() -> QuerySet[AuditLog]:
    return AuditLog.objects.select_related("user").all()
