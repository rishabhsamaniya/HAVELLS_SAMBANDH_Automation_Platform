"""Role and UserRole models for dynamic RBAC."""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from common.models.base import UUIDTimeStampedModel


class Role(UUIDTimeStampedModel):
    """Database-driven role definition."""

    name = models.CharField(max_length=100, unique=True)
    code = models.SlugField(max_length=64, unique=True, db_index=True)
    description = models.TextField(blank=True, default="")
    is_system_role = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "roles_role"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class UserRole(models.Model):
    """Maps internal users to one or more active roles."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_roles",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name="role_users",
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_user_roles",
    )
    assigned_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "roles_userrole"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "role"],
                name="uq_user_role_pair",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "role"], name="idx_userrole_user_role"),
        ]

    def __str__(self) -> str:
        return f"{self.user_id} -> {self.role.code}"
