from django.urls import path

from apps.audit_logs.views import AuditLogDetailView, AuditLogListView

urlpatterns = [
    path("", AuditLogListView.as_view(), name="audit-logs-list"),
    path("<uuid:pk>/", AuditLogDetailView.as_view(), name="audit-logs-detail"),
]
