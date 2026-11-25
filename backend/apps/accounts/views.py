"""Views for Authentication and User Management."""
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.accounts.selectors import get_user_recent_activity, get_users_queryset
from apps.accounts.serializers import (
    AdminResetPasswordSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    LogoutSerializer,
    ProfileSerializer,
    RefreshTokenSerializer,
    ResetPasswordConfirmSerializer,
    UserCreateSerializer,
    UserDetailSerializer,
    UserUpdateSerializer,
)
from apps.accounts.services import (
    activate_internal_user,
    admin_reset_user_password,
    authenticate_user,
    change_user_password,
    confirm_password_reset,
    create_internal_user,
    deactivate_internal_user,
    logout_user,
    refresh_auth_tokens,
    request_password_reset,
    update_internal_user,
)
from common.permissions.rbac import HasModulePermission
from common.responses.api import success_response


def _set_refresh_cookie(response, refresh_token: str) -> None:
    response.set_cookie(
        key=getattr(settings, "AUTH_COOKIE_REFRESH_NAME", "hs_refresh_token"),
        value=refresh_token,
        httponly=getattr(settings, "AUTH_COOKIE_HTTP_ONLY", True),
        secure=getattr(settings, "AUTH_COOKIE_SECURE", False),
        samesite=getattr(settings, "AUTH_COOKIE_SAMESITE", "Lax"),
        path="/api/v1/auth/",
        max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
    )


def _clear_refresh_cookie(response) -> None:
    response.delete_cookie(
        key=getattr(settings, "AUTH_COOKIE_REFRESH_NAME", "hs_refresh_token"),
        path="/api/v1/auth/",
    )


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "login"

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = authenticate_user(
            mobile_number=serializer.validated_data["mobile_number"],
            password=serializer.validated_data["password"],
        )
        response = success_response(
            data={
                "access": result["access"],
                "user": ProfileSerializer(result["user"]).data,
            },
            message="Login successful.",
        )
        _set_refresh_cookie(response, result["refresh"])
        return response


class RefreshTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cookie_name = getattr(settings, "AUTH_COOKIE_REFRESH_NAME", "hs_refresh_token")
        raw_refresh = serializer.validated_data.get("refresh") or request.COOKIES.get(cookie_name, "")
        result = refresh_auth_tokens(raw_refresh_token=raw_refresh)
        response = success_response(
            data={"access": result["access"]},
            message="Token refreshed successfully.",
        )
        _set_refresh_cookie(response, result["refresh"])
        return response


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cookie_name = getattr(settings, "AUTH_COOKIE_REFRESH_NAME", "hs_refresh_token")
        raw_refresh = request.COOKIES.get(cookie_name) or serializer.validated_data.get("refresh")
        logout_user(user=request.user, raw_refresh_token=raw_refresh)
        response = success_response(message="Logged out successfully.")
        _clear_refresh_cookie(response)
        return response


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return success_response(data=ProfileSerializer(request.user).data)

    def patch(self, request):
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(data=serializer.data, message="Profile updated successfully.")


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        change_user_password(
            user=request.user,
            current_password=serializer.validated_data["current_password"],
            new_password=serializer.validated_data["new_password"],
        )
        return success_response(message="Password changed successfully.")


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "login"

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        debug_data = request_password_reset(mobile_number=serializer.validated_data["mobile_number"])
        return success_response(
            data=debug_data or None,
            message="If an active account exists for this mobile number, password reset instructions have been issued.",
        )


class ResetPasswordConfirmView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "login"

    def post(self, request):
        serializer = ResetPasswordConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        confirm_password_reset(
            uid=serializer.validated_data["uid"],
            token=serializer.validated_data["token"],
            new_password=serializer.validated_data["new_password"],
        )
        return success_response(message="Password has been reset successfully.")


class UserListCreateView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    method_permissions = {
        "GET": "users.view",
        "POST": ("users.add", "users.manage"),
    }
    serializer_class = UserDetailSerializer
    search_fields = ["full_name", "mobile_number", "email"]
    filterset_fields = ["is_active", "reporting_manager"]
    ordering_fields = ["created_at", "full_name", "last_login"]

    def get_queryset(self):
        qs = get_users_queryset()
        role_code = self.request.query_params.get("role")
        if role_code:
            qs = qs.filter(user_roles__role__code=role_code, user_roles__role__is_active=True).distinct()
        return qs

    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = create_internal_user(
            actor=request.user,
            **serializer.validated_data,
        )
        return success_response(
            data=UserDetailSerializer(user).data,
            message="User created successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class UserDetailUpdateView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    method_permissions = {
        "GET": "users.view",
        "PATCH": ("users.edit", "users.manage"),
    }

    def get(self, request, pk):
        user = get_object_or_404(get_users_queryset(), pk=pk)
        return success_response(data=UserDetailSerializer(user).data)

    def patch(self, request, pk):
        target_user = get_object_or_404(get_users_queryset(), pk=pk)
        serializer = UserUpdateSerializer(
            data=request.data,
            partial=True,
            context={"target_user": target_user},
        )
        serializer.is_valid(raise_exception=True)
        updated = update_internal_user(
            actor=request.user,
            target_user=target_user,
            validated_data=serializer.validated_data,
        )
        return success_response(
            data=UserDetailSerializer(updated).data,
            message="User updated successfully.",
        )


class UserDeactivateView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    required_permission = "users.manage"

    def post(self, request, pk):
        target_user = get_object_or_404(User, pk=pk)
        updated = deactivate_internal_user(actor=request.user, target_user=target_user)
        return success_response(
            data=UserDetailSerializer(updated).data,
            message="User deactivated successfully.",
        )


class UserActivateView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    required_permission = "users.manage"

    def post(self, request, pk):
        target_user = get_object_or_404(User, pk=pk)
        updated = activate_internal_user(actor=request.user, target_user=target_user)
        return success_response(
            data=UserDetailSerializer(updated).data,
            message="User activated successfully.",
        )


class UserAdminResetPasswordView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    required_permission = "users.manage"

    def post(self, request, pk):
        target_user = get_object_or_404(User, pk=pk)
        serializer = AdminResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        admin_reset_user_password(
            actor=request.user,
            target_user=target_user,
            new_password=serializer.validated_data["new_password"],
        )
        return success_response(message="User password reset successfully.")


class UserActivityView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    required_permission = "users.view"

    def get(self, request, pk):
        target_user = get_object_or_404(User, pk=pk)
        logs = get_user_recent_activity(target_user)
        data = [
            {
                "id": str(log.id),
                "action": log.action,
                "module": log.module,
                "object_type": log.object_type,
                "object_id": log.object_id,
                "ip_address": log.ip_address,
                "created_at": log.created_at,
            }
            for log in logs
        ]
        return success_response(data=data)
