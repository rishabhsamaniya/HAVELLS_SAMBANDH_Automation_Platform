from django.contrib import admin

from apps.audit_logs.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "module", "action", "object_type", "object_id", "ip_address")
    list_filter = ("module", "action", "object_type")
    search_fields = ("action", "object_id", "user__full_name", "user__mobile_number")
    readonly_fields = (
        "id",
        "user",
        "action",
        "module",
        "object_type",
        "object_id",
        "old_values",
        "new_values",
        "ip_address",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
