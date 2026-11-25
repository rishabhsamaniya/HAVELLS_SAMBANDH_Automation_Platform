"""Serializers for Role Management."""
from rest_framework import serializers

from apps.permissions.serializers import PermissionSerializer
from apps.roles.models import Role


class RoleSerializer(serializers.ModelSerializer):
    users_count = serializers.IntegerField(read_only=True, default=0)
    permissions_count = serializers.IntegerField(read_only=True, default=0)
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = [
            "id",
            "name",
            "code",
            "description",
            "is_system_role",
            "is_active",
            "users_count",
            "permissions_count",
            "permissions",
            "created_at",
            "updated_at",
        ]

    def get_permissions(self, obj: Role) -> list[dict]:
        perms = [rp.permission for rp in obj.role_permissions.all()]
        return PermissionSerializer(perms, many=True).data


class RoleCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    code = serializers.SlugField(max_length=64)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    is_active = serializers.BooleanField(required=False, default=True)

    def validate_code(self, value: str) -> str:
        normalized = value.strip().lower()
        if Role.objects.filter(code=normalized).exists():
            raise serializers.ValidationError("A role with this code already exists.")
        return normalized

    def validate_name(self, value: str) -> str:
        cleaned = value.strip()
        if Role.objects.filter(name__iexact=cleaned).exists():
            raise serializers.ValidationError("A role with this name already exists.")
        return cleaned


class RoleUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)
