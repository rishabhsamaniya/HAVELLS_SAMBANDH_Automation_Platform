"""Read-only serializer for AuditLog records."""
from rest_framework import serializers

from apps.audit_logs.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True, default="System / Public")
    user_mobile = serializers.CharField(source="user.mobile_number", read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "user",
            "user_name",
            "user_mobile",
            "action",
            "module",
            "object_type",
            "object_id",
            "old_values",
            "new_values",
            "ip_address",
            "created_at",
        ]
        read_only_fields = fields
