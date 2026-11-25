"""Selectors for Permission catalog."""
from django.db.models import QuerySet

from apps.permissions.models import Permission


def get_permissions_queryset() -> QuerySet[Permission]:
    return Permission.objects.all().order_by("module", "action", "codename")
