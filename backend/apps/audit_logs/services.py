"""Audit logging service with automatic secret redaction."""
from typing import Any

from apps.audit_logs.models import AuditLog
from common.middleware.request_context import get_request_context

REDACTED_KEYS = {
    "password",
    "new_password",
    "current_password",
    "old_password",
    "token",
    "raw_token",
    "token_hash",
    "access",
    "refresh",
    "secret",
    "authorization",
}


def sanitize_payload(data: Any) -> Any:
    """Recursively strip/redact sensitive keys before storing in AuditLog."""
    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            if str(k).lower() in REDACTED_KEYS:
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = sanitize_payload(v)
        return sanitized
    if isinstance(data, list):
        return [sanitize_payload(item) for item in data]
    return data


def log_audit_event(
    *,
    user=None,
    action: str,
    module: str,
    object_type: str,
    object_id: str = "",
    old_values: dict | None = None,
    new_values: dict | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Create an immutable AuditLog record with sanitized JSON payloads."""
    ctx = get_request_context()
    resolved_ip = ip_address if ip_address is not None else (ctx.get("ip_address") or None)
    actor = user if (user is not None and getattr(user, "is_authenticated", False)) else None

    return AuditLog.objects.create(
        user=actor,
        action=action,
        module=module,
        object_type=object_type,
        object_id=str(object_id) if object_id else "",
        old_values=sanitize_payload(old_values) if old_values is not None else None,
        new_values=sanitize_payload(new_values) if new_values is not None else None,
        ip_address=resolved_ip,
    )
