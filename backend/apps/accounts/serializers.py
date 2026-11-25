"""Serializers for Authentication and User Management."""
from rest_framework import serializers

from apps.accounts.models import User
from apps.accounts.selectors import (
    get_user_effective_permissions,
    get_user_effective_roles,
)
from common.validators.mobile import normalize_indian_mobile, validate_indian_mobile


class MobileFieldMixin:
    def validate_mobile_number(self, value: str) -> str:
        normalized = normalize_indian_mobile(value)
        validate_indian_mobile(normalized)
        return normalized


class LoginSerializer(MobileFieldMixin, serializers.Serializer):
    mobile_number = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=False, allow_blank=True)


class RefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=False, allow_blank=True)


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)


class ForgotPasswordSerializer(MobileFieldMixin, serializers.Serializer):
    mobile_number = serializers.CharField(max_length=20)


class ResetPasswordConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)


class AdminResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)


class ProfileSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "full_name",
            "mobile_number",
            "email",
            "is_active",
            "is_superuser",
            "last_login",
            "date_joined",
            "roles",
            "permissions",
        ]
        read_only_fields = [
            "id",
            "mobile_number",
            "is_active",
            "is_superuser",
            "last_login",
            "date_joined",
            "roles",
            "permissions",
        ]

    def get_roles(self, obj: User) -> list[dict]:
        return get_user_effective_roles(obj)

    def get_permissions(self, obj: User) -> list[str]:
        return get_user_effective_permissions(obj)


class UserDetailSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    reporting_manager_name = serializers.CharField(
        source="reporting_manager.full_name",
        read_only=True,
        default=None,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "full_name",
            "mobile_number",
            "email",
            "reporting_manager",
            "reporting_manager_name",
            "is_active",
            "is_staff",
            "is_superuser",
            "last_login",
            "date_joined",
            "created_at",
            "updated_at",
            "roles",
        ]

    def get_roles(self, obj: User) -> list[dict]:
        return get_user_effective_roles(obj)


class UserCreateSerializer(MobileFieldMixin, serializers.Serializer):
    full_name = serializers.CharField(max_length=150)
    mobile_number = serializers.CharField(max_length=20)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    password = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)
    reporting_manager = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    role_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=list,
    )
    is_active = serializers.BooleanField(required=False, default=True)

    def validate_mobile_number(self, value: str) -> str:
        normalized = super().validate_mobile_number(value)
        if User.objects.filter(mobile_number=normalized).exists():
            raise serializers.ValidationError("A user with this mobile number already exists.")
        return normalized


class UserUpdateSerializer(MobileFieldMixin, serializers.Serializer):
    full_name = serializers.CharField(max_length=150, required=False)
    mobile_number = serializers.CharField(max_length=20, required=False)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    reporting_manager = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    role_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
    )
    is_active = serializers.BooleanField(required=False)

    def validate_mobile_number(self, value: str) -> str:
        normalized = super().validate_mobile_number(value)
        target_user = self.context.get("target_user")
        qs = User.objects.filter(mobile_number=normalized)
        if target_user is not None:
            qs = qs.exclude(pk=target_user.pk)
        if qs.exists():
            raise serializers.ValidationError("A user with this mobile number already exists.")
        return normalized
