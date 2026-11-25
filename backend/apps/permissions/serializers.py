"""Serializers for Permissions."""
from rest_framework import serializers

from apps.permissions.models import Permission


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "name", "codename", "module", "action", "description"]


class RolePermissionsUpdateSerializer(serializers.Serializer):
    permission_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=True,
    )
