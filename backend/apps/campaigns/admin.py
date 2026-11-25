from django.contrib import admin

from apps.campaigns.models import Campaign


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ("campaign_name", "campaign_code", "start_date", "end_date", "timezone", "status")
    list_filter = ("status", "timezone")
    search_fields = ("campaign_name", "campaign_code")
    readonly_fields = ("id", "created_at", "updated_at")
