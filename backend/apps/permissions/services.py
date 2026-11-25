"""Centralized backend RBAC permission evaluation and queryset scoping service."""
from django.db import transaction
from django.db.models import QuerySet

from apps.accounts.models import User
from apps.audit_logs.services import log_audit_event
from apps.permissions.models import Permission, RolePermission
from apps.roles.models import Role
from common.exceptions.domain import DomainError


class PermissionService:
    """Single source of truth for backend authorization and RM data isolation."""

    @staticmethod
    def is_super_admin(user: User) -> bool:
        if not user or not getattr(user, "is_authenticated", False) or not user.is_active:
            return False
        if user.is_superuser:
            return True
        return user.user_roles.filter(role__code="super_admin", role__is_active=True).exists()

    @classmethod
    def get_user_permissions(cls, user: User) -> set[str]:
        if not user or not getattr(user, "is_authenticated", False) or not user.is_active:
            return set()
        if cls.is_super_admin(user):
            return {"*"}

        active_role_ids = user.user_roles.filter(role__is_active=True).values_list(
            "role_id", flat=True
        )
        return set(
            Permission.objects.filter(
                permission_roles__role_id__in=active_role_ids
            ).values_list("codename", flat=True)
        )

    @classmethod
    def has_permission(cls, user: User, codename: str) -> bool:
        perms = cls.get_user_permissions(user)
        return "*" in perms or codename in perms

    @classmethod
    def has_any_permission(cls, user: User, codenames: list[str] | tuple[str, ...]) -> bool:
        perms = cls.get_user_permissions(user)
        if "*" in perms:
            return True
        return any(code in perms for code in codenames)

    @classmethod
    def can_access_all_dealers(cls, user: User) -> bool:
        return cls.has_permission(user, "dealers.view_all")

    @classmethod
    def scope_dealer_queryset(
        cls,
        user: User,
        queryset: QuerySet,
        rm_field: str = "assigned_rm",
    ) -> QuerySet:
        """Enforce strict RM data isolation unless user holds org-wide dealer visibility."""
        if cls.can_access_all_dealers(user):
            return queryset
        return queryset.filter(**{rm_field: user})


@transaction.atomic
def assign_permissions_to_role(*, actor: User, role: Role, permission_ids: list) -> Role:
    """Replace a role's assigned permissions dynamically and record an audit event."""
    old_codes = sorted(
        role.role_permissions.select_related("permission").values_list(
            "permission__codename", flat=True
        )
    )
    permissions = list(Permission.objects.filter(id__in=permission_ids))
    if len(permissions) != len(set(str(pid) for pid in permission_ids)):
        raise DomainError(
            message="One or more permission IDs are invalid.",
            code="INVALID_PERMISSION",
        )

    RolePermission.objects.filter(role=role).delete()
    RolePermission.objects.bulk_create(
        [RolePermission(role=role, permission=perm) for perm in permissions]
    )
    new_codes = sorted(perm.codename for perm in permissions)

    log_audit_event(
        user=actor,
        action="ROLE_PERMISSIONS_UPDATED",
        module="permissions",
        object_type="Role",
        object_id=str(role.id),
        old_values={"role_code": role.code, "permissions": old_codes},
        new_values={"role_code": role.code, "permissions": new_codes},
    )
    return role
