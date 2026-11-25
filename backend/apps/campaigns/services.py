"""Business logic services for Campaigns."""
from django.db import transaction

from apps.accounts.models import User
from apps.audit_logs.services import log_audit_event
from apps.campaigns.models import Campaign


@transaction.atomic
def create_campaign(*, actor: User, validated_data: dict) -> Campaign:
    campaign = Campaign.objects.create(created_by=actor, **validated_data)
    log_audit_event(
        user=actor,
        action="CAMPAIGN_CREATED",
        module="campaigns",
        object_type="Campaign",
        object_id=str(campaign.id),
        new_values={
            "campaign_name": campaign.campaign_name,
            "campaign_code": campaign.campaign_code,
            "start_date": campaign.start_date.isoformat(),
            "end_date": campaign.end_date.isoformat(),
            "status": campaign.status,
        },
    )
    return campaign


@transaction.atomic
def update_campaign(*, actor: User, campaign: Campaign, validated_data: dict) -> Campaign:
    old_values = {
        "campaign_name": campaign.campaign_name,
        "status": campaign.status,
        "start_date": campaign.start_date.isoformat(),
        "end_date": campaign.end_date.isoformat(),
    }
    for field, value in validated_data.items():
        setattr(campaign, field, value)
    campaign.save()

    log_audit_event(
        user=actor,
        action="CAMPAIGN_UPDATED",
        module="campaigns",
        object_type="Campaign",
        object_id=str(campaign.id),
        old_values=old_values,
        new_values={
            "campaign_name": campaign.campaign_name,
            "status": campaign.status,
            "start_date": campaign.start_date.isoformat(),
            "end_date": campaign.end_date.isoformat(),
        },
    )
    return campaign
