from django.contrib import admin

from apps.dealers.models import Dealer


@admin.register(Dealer)
class DealerAdmin(admin.ModelAdmin):
    list_display = ("dealer_code", "mobile_number", "status", "assigned_rm", "created_at")
    list_filter = ("status", "assigned_rm")
    search_fields = ("dealer_code", "mobile_number", "assigned_rm__full_name")
    autocomplete_fields = ("assigned_rm", "created_by")
    readonly_fields = ("id", "created_at", "updated_at")
