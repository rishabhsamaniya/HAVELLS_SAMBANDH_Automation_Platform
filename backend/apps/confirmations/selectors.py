"""RBAC-scoped selectors for Confirmation Links and Confirmations."""
from django.db.models import QuerySet

from apps.accounts.models import User
from apps.confirmations.models import Confirmation, ConfirmationLink
from apps.permissions.services import PermissionService


def get_scoped_confirmation_links_queryset(user: User) -> QuerySet[ConfirmationLink]:
    qs = ConfirmationLink.objects.select_related(
        "dealer", "campaign", "assigned_rm", "created_by"
    ).all()
    return PermissionService.scope_dealer_queryset(user, qs, rm_field="assigned_rm")


def get_scoped_confirmations_queryset(user: User) -> QuerySet[Confirmation]:
    qs = Confirmation.objects.select_related(
        "dealer", "dealer__assigned_rm", "campaign", "preferred_time_slot", "confirmation_link"
    ).all()
    return PermissionService.scope_dealer_queryset(user, qs, rm_field="dealer__assigned_rm")
