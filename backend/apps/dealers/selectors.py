"""Reusable RBAC-scoped read queries for Dealers."""
from django.db.models import QuerySet

from apps.accounts.models import User
from apps.confirmations.models import Confirmation
from apps.dealers.models import Dealer
from apps.permissions.services import PermissionService


def get_scoped_dealers_queryset(user: User) -> QuerySet[Dealer]:
    qs = Dealer.objects.select_related("assigned_rm", "campaign", "created_by").all()
    return PermissionService.scope_dealer_queryset(user, qs, rm_field="assigned_rm")


def get_dealer_confirmation_history(dealer: Dealer) -> QuerySet[Confirmation]:
    return (
        Confirmation.objects.select_related("campaign", "preferred_time_slot", "confirmation_link")
        .filter(dealer=dealer)
        .order_by("-submitted_at")
    )
