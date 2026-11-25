from django.contrib import admin

from apps.confirmations.models import Confirmation, ConfirmationHistory, ConfirmationLink


@admin.register(ConfirmationLink)
class ConfirmationLinkAdmin(admin.ModelAdmin):
    list_display = (
        "dealer",
        "campaign",
        "assigned_rm",
        "allowed_month",
        "status",
        "is_regenerated",
        "regeneration_count",
        "submission_count",
        "max_submissions",
        "expires_at",
    )
    list_filter = ("status", "is_regenerated", "allowed_month", "campaign")
    search_fields = ("dealer__dealer_code", "dealer__mobile_number", "assigned_rm__full_name")
    exclude = ("encrypted_token",)
    readonly_fields = ("id", "token_hash", "created_at", "updated_at")


@admin.register(Confirmation)
class ConfirmationAdmin(admin.ModelAdmin):
    list_display = (
        "dealer",
        "campaign",
        "preferred_date",
        "preferred_time_slot",
        "submission_status",
        "remarks",
        "submitted_at",
    )
    list_filter = ("submission_status", "preferred_date", "campaign")
    search_fields = ("dealer__dealer_code", "dealer__mobile_number", "remarks")
    readonly_fields = ("id", "submitted_at", "created_at", "updated_at")


@admin.register(ConfirmationHistory)
class ConfirmationHistoryAdmin(admin.ModelAdmin):
    list_display = ("confirmation", "action", "previous_date", "new_date", "changed_by", "created_at")
    list_filter = ("action",)
    readonly_fields = (
        "id",
        "confirmation",
        "action",
        "previous_date",
        "previous_time_slot",
        "new_date",
        "new_time_slot",
        "reason",
        "changed_by",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
