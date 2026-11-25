from django.contrib import admin

from apps.scheduling.models import BlockedSlot, Holiday, OperatingHoursConfig, TimeSlot


@admin.register(OperatingHoursConfig)
class OperatingHoursConfigAdmin(admin.ModelAdmin):
    list_display = (
        "opening_time",
        "closing_time",
        "slot_duration",
        "default_capacity",
        "allow_same_day_booking",
        "is_active",
    )
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ("display_label", "start_time", "end_time", "slot_duration", "max_capacity", "is_active")
    list_filter = ("is_active",)
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ("date", "name", "is_active", "created_by")
    list_filter = ("is_active",)
    search_fields = ("name",)
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(BlockedSlot)
class BlockedSlotAdmin(admin.ModelAdmin):
    list_display = ("date", "time_slot", "reason", "is_active", "created_by")
    list_filter = ("is_active", "date")
    search_fields = ("reason",)
    readonly_fields = ("id", "created_at", "updated_at")
