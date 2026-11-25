"""Selectors for Roles."""
from django.db.models import Count, QuerySet

from apps.roles.models import Role


def get_roles_queryset() -> QuerySet[Role]:
    return (
        Role.objects.annotate(
            users_count=Count("role_users", distinct=True),
            permissions_count=Count("role_permissions", distinct=True),
        )
        .prefetch_related("role_permissions__permission")
        .order_by("name")
    )
