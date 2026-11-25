"""Immutable AuditLog model."""
import uuid

from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """Records all critical system activities without exposing secrets."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=100, db_index=True)
    module = models.CharField(max_length=64, db_index=True)
    object_type = models.CharField(max_length=100, db_index=True)
    object_id = models.CharField(max_length=64, blank=True, default="", db_index=True)
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "audit_logs_auditlog"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["module", "action"], name="idx_audit_module_action"),
            models.Index(fields=["object_type", "object_id"], name="idx_audit_object"),
            models.Index(fields=["user", "created_at"], name="idx_audit_user_created"),
        ]

    def __str__(self) -> str:
        return f"[{self.module}] {self.action} ({self.object_type}:{self.object_id})"
