"""Business logic services for Roles."""
from django.db import transaction

from apps.accounts.models import User
from apps.audit_logs.services import log_audit_event
from apps.roles.models import Role
from common.exceptions.domain import ForbiddenError


@transaction.atomic
def create_role(*, actor: User, name: str, code: str, description: str = "", is_active: bool = True) -> Role:
    role = Role.objects.create(
        name=name.strip(),
        code=code.strip().lower(),
        description=description.strip(),
        is_active=is_active,
        is_system_role=False,
    )
    log_audit_event(
        user=actor,
        action="ROLE_CREATED",
        module="roles",
        object_type="Role",
        object_id=str(role.id),
        new_values={"name": role.name, "code": role.code, "is_active": role.is_active},
    )
    return role


@transaction.atomic
def update_role(*, actor: User, role: Role, validated_data: dict) -> Role:
    if role.code == "super_admin" and validated_data.get("is_active") is False:
        raise ForbiddenError(
            message="The Super Admin system role cannot be deactivated.",
            code="SYSTEM_ROLE_PROTECTED",
        )

    old_values = {
        "name": role.name,
        "description": role.description,
        "is_active": role.is_active,
    }
    for field, value in validated_data.items():
        if field == "code" and role.is_system_role:
            continue
        setattr(role, field, value)
    role.save()

    log_audit_event(
        user=actor,
        action="ROLE_UPDATED",
        module="roles",
        object_type="Role",
        object_id=str(role.id),
        old_values=old_values,
        new_values={
            "name": role.name,
            "description": role.description,
            "is_active": role.is_active,
        },
    )
    return role
