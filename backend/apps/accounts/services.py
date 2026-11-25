"""Authentication and User Management business logic services."""
from datetime import timedelta
import logging

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import status
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.audit_logs.services import log_audit_event
from apps.roles.models import Role, UserRole
from common.exceptions.domain import DomainError, ForbiddenError
from common.validators.mobile import normalize_indian_mobile

logger = logging.getLogger(__name__)
password_reset_token_generator = PasswordResetTokenGenerator()


def authenticate_user(*, mobile_number: str, password: str) -> dict:
    """Authenticate internal user by 10-digit mobile_number + password with lockout protection."""
    normalized_mobile = normalize_indian_mobile(mobile_number)
    user = User.objects.filter(mobile_number=normalized_mobile).first()

    if user is None:
        raise DomainError(
            message="Invalid mobile number or password.",
            code="INVALID_CREDENTIALS",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active:
        log_audit_event(
            user=user,
            action="LOGIN_BLOCKED_INACTIVE",
            module="accounts",
            object_type="User",
            object_id=str(user.id),
        )
        raise DomainError(
            message="Your account is deactivated. Please contact your administrator.",
            code="ACCOUNT_DEACTIVATED",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    now = timezone.now()
    if user.locked_until and user.locked_until > now:
        remaining_minutes = max(1, int((user.locked_until - now).total_seconds() // 60) + 1)
        raise DomainError(
            message=f"Account temporarily locked due to failed logins. Try again in {remaining_minutes} minute(s).",
            code="ACCOUNT_LOCKED",
            status_code=status.HTTP_423_LOCKED,
        )

    if not user.check_password(password):
        user.failed_login_attempts += 1
        max_attempts = getattr(settings, "AUTH_MAX_FAILED_LOGINS", 5)
        lockout_minutes = getattr(settings, "AUTH_LOCKOUT_MINUTES", 15)
        if user.failed_login_attempts >= max_attempts:
            user.locked_until = now + timedelta(minutes=lockout_minutes)
        user.save(update_fields=["failed_login_attempts", "locked_until", "updated_at"])

        log_audit_event(
            user=user,
            action="LOGIN_FAILED",
            module="accounts",
            object_type="User",
            object_id=str(user.id),
            new_values={"failed_login_attempts": user.failed_login_attempts},
        )
        raise DomainError(
            message="Invalid mobile number or password.",
            code="INVALID_CREDENTIALS",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    # Successful login: reset lockout counters and issue JWT pair
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = now
    user.save(update_fields=["failed_login_attempts", "locked_until", "last_login", "updated_at"])

    refresh = RefreshToken.for_user(user)
    log_audit_event(
        user=user,
        action="LOGIN_SUCCESS",
        module="accounts",
        object_type="User",
        object_id=str(user.id),
    )

    return {
        "user": user,
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


def refresh_auth_tokens(*, raw_refresh_token: str) -> dict:
    """Validate and rotate refresh token, verifying user is still active."""
    if not raw_refresh_token:
        raise DomainError(
            message="Refresh token is required.",
            code="REFRESH_TOKEN_MISSING",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    try:
        token = RefreshToken(raw_refresh_token)
        user_id = token.get("user_id")
        user = User.objects.filter(id=user_id, is_active=True).first()
        if not user:
            raise DomainError(
                message="User account is inactive or no longer exists.",
                code="ACCOUNT_INACTIVE",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        if getattr(settings, "SIMPLE_JWT", {}).get("ROTATE_REFRESH_TOKENS", True):
            if getattr(settings, "SIMPLE_JWT", {}).get("BLACKLIST_AFTER_ROTATION", True):
                token.blacklist()
            new_refresh = RefreshToken.for_user(user)
            return {
                "access": str(new_refresh.access_token),
                "refresh": str(new_refresh),
            }

        return {
            "access": str(token.access_token),
            "refresh": str(token),
        }
    except TokenError as exc:
        raise DomainError(
            message="Invalid or expired refresh token.",
            code="INVALID_REFRESH_TOKEN",
            status_code=status.HTTP_401_UNAUTHORIZED,
        ) from exc


def logout_user(*, user: User | None, raw_refresh_token: str | None) -> None:
    """Blacklist the provided refresh token on logout."""
    if raw_refresh_token:
        try:
            token = RefreshToken(raw_refresh_token)
            token.blacklist()
        except TokenError:
            # Already invalid or expired; proceed with cookie clearing
            pass

    if user and user.is_authenticated:
        log_audit_event(
            user=user,
            action="LOGOUT",
            module="accounts",
            object_type="User",
            object_id=str(user.id),
        )


def change_user_password(*, user: User, current_password: str, new_password: str) -> None:
    """Change authenticated user's password after verifying current password."""
    if not user.check_password(current_password):
        raise DomainError(
            message="Current password is incorrect.",
            code="INVALID_CURRENT_PASSWORD",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"current_password": ["Current password is incorrect."]},
        )

    try:
        validate_password(new_password, user=user)
    except DjangoValidationError as exc:
        raise DomainError(
            message="New password does not meet security requirements.",
            code="WEAK_PASSWORD",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"new_password": list(exc.messages)},
        ) from exc

    user.set_password(new_password)
    user.save(update_fields=["password", "updated_at"])

    log_audit_event(
        user=user,
        action="PASSWORD_CHANGED",
        module="accounts",
        object_type="User",
        object_id=str(user.id),
    )


def request_password_reset(*, mobile_number: str) -> dict:
    """Initiate forgot-password workflow without revealing whether account exists."""
    normalized_mobile = normalize_indian_mobile(mobile_number)
    user = User.objects.filter(mobile_number=normalized_mobile, is_active=True).first()

    reset_payload = {}
    if user:
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = password_reset_token_generator.make_token(user)
        logger.info("Password reset requested for user=%s (uid=%s)", user.id, uid)
        log_audit_event(
            user=user,
            action="PASSWORD_RESET_REQUESTED",
            module="accounts",
            object_type="User",
            object_id=str(user.id),
        )
        if settings.DEBUG:
            reset_payload = {"uid": uid, "token": token}

    return reset_payload


def confirm_password_reset(*, uid: str, token: str, new_password: str) -> None:
    """Complete forgot-password reset using signed Django reset token."""
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id, is_active=True)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist) as exc:
        raise DomainError(
            message="Invalid or expired password reset link.",
            code="INVALID_RESET_TOKEN",
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc

    if not password_reset_token_generator.check_token(user, token):
        raise DomainError(
            message="Invalid or expired password reset link.",
            code="INVALID_RESET_TOKEN",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        validate_password(new_password, user=user)
    except DjangoValidationError as exc:
        raise DomainError(
            message="New password does not meet security requirements.",
            code="WEAK_PASSWORD",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"new_password": list(exc.messages)},
        ) from exc

    user.set_password(new_password)
    user.failed_login_attempts = 0
    user.locked_until = None
    user.save(update_fields=["password", "failed_login_attempts", "locked_until", "updated_at"])

    log_audit_event(
        user=user,
        action="PASSWORD_RESET_COMPLETED",
        module="accounts",
        object_type="User",
        object_id=str(user.id),
    )


@transaction.atomic
def create_internal_user(
    *,
    actor: User,
    full_name: str,
    mobile_number: str,
    password: str,
    email: str | None = None,
    reporting_manager: User | None = None,
    role_ids: list | None = None,
    is_active: bool = True,
) -> User:
    """Create an internal user, assign roles, and record audit log."""
    try:
        validate_password(password)
    except DjangoValidationError as exc:
        raise DomainError(
            message="Password does not meet security requirements.",
            code="WEAK_PASSWORD",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"password": list(exc.messages)},
        ) from exc

    user = User.objects.create_user(
        mobile_number=mobile_number,
        full_name=full_name,
        password=password,
        email=email or None,
        reporting_manager=reporting_manager,
        is_active=is_active,
    )

    assigned_role_codes = []
    if role_ids:
        roles = list(Role.objects.filter(id__in=role_ids, is_active=True))
        if len(roles) != len(set(str(r) for r in role_ids)):
            raise DomainError(
                message="One or more specified roles are invalid or inactive.",
                code="INVALID_ROLE",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        for role in roles:
            UserRole.objects.create(user=user, role=role, assigned_by=actor)
            assigned_role_codes.append(role.code)

    log_audit_event(
        user=actor,
        action="USER_CREATED",
        module="accounts",
        object_type="User",
        object_id=str(user.id),
        new_values={
            "full_name": user.full_name,
            "mobile_number": user.mobile_number,
            "email": user.email,
            "roles": assigned_role_codes,
            "is_active": user.is_active,
        },
    )
    return user


@transaction.atomic
def update_internal_user(
    *,
    actor: User,
    target_user: User,
    validated_data: dict,
) -> User:
    """Update user profile, reporting manager, and optionally replace assigned roles."""
    old_values = {
        "full_name": target_user.full_name,
        "mobile_number": target_user.mobile_number,
        "email": target_user.email,
        "reporting_manager_id": str(target_user.reporting_manager_id) if target_user.reporting_manager_id else None,
        "is_active": target_user.is_active,
        "roles": list(target_user.user_roles.values_list("role__code", flat=True)),
    }

    role_ids = validated_data.pop("role_ids", None)
    for field, value in validated_data.items():
        setattr(target_user, field, value)
    target_user.save()

    if role_ids is not None:
        roles = list(Role.objects.filter(id__in=role_ids, is_active=True))
        if len(roles) != len(set(str(r) for r in role_ids)):
            raise DomainError(
                message="One or more specified roles are invalid or inactive.",
                code="INVALID_ROLE",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        UserRole.objects.filter(user=target_user).delete()
        for role in roles:
            UserRole.objects.create(user=target_user, role=role, assigned_by=actor)

    new_values = {
        "full_name": target_user.full_name,
        "mobile_number": target_user.mobile_number,
        "email": target_user.email,
        "reporting_manager_id": str(target_user.reporting_manager_id) if target_user.reporting_manager_id else None,
        "is_active": target_user.is_active,
        "roles": list(target_user.user_roles.values_list("role__code", flat=True)),
    }

    log_audit_event(
        user=actor,
        action="USER_UPDATED",
        module="accounts",
        object_type="User",
        object_id=str(target_user.id),
        old_values=old_values,
        new_values=new_values,
    )
    return target_user


@transaction.atomic
def deactivate_internal_user(*, actor: User, target_user: User) -> User:
    """Deactivate a user with self-deactivation and last-superuser guards."""
    if actor.id == target_user.id:
        raise ForbiddenError(
            message="You cannot deactivate your own account.",
            code="SELF_DEACTIVATION_FORBIDDEN",
        )

    if target_user.is_superuser:
        other_active_superusers = User.objects.filter(
            is_superuser=True, is_active=True
        ).exclude(id=target_user.id)
        if not other_active_superusers.exists():
            raise ForbiddenError(
                message="Cannot deactivate the last active Super Admin account.",
                code="LAST_SUPERADMIN_FORBIDDEN",
            )

    target_user.is_active = False
    target_user.save(update_fields=["is_active", "updated_at"])

    log_audit_event(
        user=actor,
        action="USER_DEACTIVATED",
        module="accounts",
        object_type="User",
        object_id=str(target_user.id),
        old_values={"is_active": True},
        new_values={"is_active": False},
    )
    return target_user


@transaction.atomic
def activate_internal_user(*, actor: User, target_user: User) -> User:
    """Reactivate a deactivated user and clear lockout state."""
    target_user.is_active = True
    target_user.failed_login_attempts = 0
    target_user.locked_until = None
    target_user.save(update_fields=["is_active", "failed_login_attempts", "locked_until", "updated_at"])

    log_audit_event(
        user=actor,
        action="USER_ACTIVATED",
        module="accounts",
        object_type="User",
        object_id=str(target_user.id),
        old_values={"is_active": False},
        new_values={"is_active": True},
    )
    return target_user


@transaction.atomic
def admin_reset_user_password(*, actor: User, target_user: User, new_password: str) -> None:
    """Allow authorized admin to reset another user's password."""
    try:
        validate_password(new_password, user=target_user)
    except DjangoValidationError as exc:
        raise DomainError(
            message="Password does not meet security requirements.",
            code="WEAK_PASSWORD",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"new_password": list(exc.messages)},
        ) from exc

    target_user.set_password(new_password)
    target_user.failed_login_attempts = 0
    target_user.locked_until = None
    target_user.save(update_fields=["password", "failed_login_attempts", "locked_until", "updated_at"])

    log_audit_event(
        user=actor,
        action="ADMIN_PASSWORD_RESET",
        module="accounts",
        object_type="User",
        object_id=str(target_user.id),
    )
