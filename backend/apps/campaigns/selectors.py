"""Selectors for Campaigns."""
from django.db.models import QuerySet

from apps.campaigns.models import Campaign


def get_campaigns_queryset() -> QuerySet[Campaign]:
    return Campaign.objects.select_related("created_by").all()
