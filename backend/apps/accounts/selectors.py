"""Reusable read queries for accounts."""
from django.db.models import QuerySet

from apps.accounts.models import User
from apps.audit_logs.models import AuditLog


def get_users_queryset() -> QuerySet[User]:
    return (
        User.objects.select_related("reporting_manager")
        .prefetch_related("user_roles__role")
        .all()
    )


def get_user_effective_roles(user: User) -> list[dict]:
    user_roles = (
        user.user_roles.select_related("role")
        .filter(role__is_active=True)
        .order_by("role__name")
    )
    return [
        {"id": str(ur.role.id), "name": ur.role.name, "code": ur.role.code}
        for ur in user_roles
    ]


def get_user_effective_permissions(user: User) -> list[str]:
    from apps.permissions.services import PermissionService

    return sorted(PermissionService.get_user_permissions(user))


def get_user_recent_activity(user: User, limit: int = 25) -> QuerySet[AuditLog]:
    return AuditLog.objects.filter(user=user).order_by("-created_at")[:limit]
