"""Permission and RolePermission models for dynamic RBAC."""
import uuid

from django.db import models

from apps.roles.models import Role
from common.models.base import UUIDTimeStampedModel


class PermissionAction(models.TextChoices):
    VIEW = "view", "View"
    ADD = "add", "Add"
    EDIT = "edit", "Edit"
    DELETE = "delete", "Delete"
    IMPORT = "import", "Import"
    EXPORT = "export", "Export"
    APPROVE = "approve", "Approve"
    MANAGE = "manage", "Manage"


class Permission(UUIDTimeStampedModel):
    """Granular module-action permission (e.g., dealers.import)."""

    name = models.CharField(max_length=120)
    codename = models.CharField(max_length=100, unique=True, db_index=True)
    module = models.CharField(max_length=64, db_index=True)
    action = models.CharField(
        max_length=32,
        choices=PermissionAction.choices,
        default=PermissionAction.VIEW,
        db_index=True,
    )
    description = models.TextField(blank=True, default="")

    class Meta:
        db_table = "permissions_permission"
        ordering = ["module", "action", "codename"]
        indexes = [
            models.Index(fields=["module", "action"], name="idx_perm_module_action"),
        ]

    def __str__(self) -> str:
        return self.codename


class RolePermission(models.Model):
    """Maps a Role to its granted Permissions."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="role_permissions",
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name="permission_roles",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "permissions_rolepermission"
        constraints = [
            models.UniqueConstraint(
                fields=["role", "permission"],
                name="uq_role_permission_pair",
            ),
        ]
        indexes = [
            models.Index(fields=["role", "permission"], name="idx_roleperm_pair"),
        ]

    def __str__(self) -> str:
        return f"{self.role.code} -> {self.permission.codename}"
