"""Serializers for Scheduling Management."""
from datetime import time

from rest_framework import serializers

from apps.campaigns.models import Campaign
from apps.confirmations.models import Confirmation, ConfirmationHistory
from apps.dealers.models import Dealer
from apps.scheduling.models import BlockedSlot, Holiday, OperatingHoursConfig, TimeSlot


class OperatingHoursConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperatingHoursConfig
        fields = [
            "id",
            "opening_time",
            "closing_time",
            "slot_duration",
            "default_capacity",
            "allow_same_day_booking",
            "is_active",
            "updated_at",
        ]
        read_only_fields = ["id", "is_active", "updated_at"]

    def validate(self, attrs):
        opening = attrs.get("opening_time", getattr(self.instance, "opening_time", None))
        closing = attrs.get("closing_time", getattr(self.instance, "closing_time", None))
        if opening is not None and closing is not None:
            is_midnight_close = closing == time(0, 0)
            if not is_midnight_close and closing <= opening:
                raise serializers.ValidationError(
                    {"closing_time": "Closing time must be after opening time (or 00:00 for 24-hour / midnight close)."}
                )
        return attrs


class TimeSlotSerializer(serializers.ModelSerializer):
    display_label = serializers.CharField(read_only=True)

    class Meta:
        model = TimeSlot
        fields = [
            "id",
            "start_time",
            "end_time",
            "display_label",
            "slot_duration",
            "max_capacity",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "display_label", "created_at", "updated_at"]

    def validate(self, attrs):
        start = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end = attrs.get("end_time", getattr(self.instance, "end_time", None))
        if start is not None and end is not None:
            is_midnight_end = end == time(0, 0) and start > time(0, 0)
            if not is_midnight_end and end <= start:
                raise serializers.ValidationError(
                    {"end_time": "End time must be after start time (or 00:00 for midnight)."}
                )
        return attrs


class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Holiday
        fields = ["id", "date", "name", "description", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


class BlockedSlotSerializer(serializers.ModelSerializer):
    time_slot_label = serializers.CharField(source="time_slot.display_label", read_only=True)

    class Meta:
        model = BlockedSlot
        fields = ["id", "date", "time_slot", "time_slot_label", "reason", "is_active", "created_at"]
        read_only_fields = ["id", "time_slot_label", "created_at"]


class BookingSerializer(serializers.ModelSerializer):
    dealer_code = serializers.CharField(source="dealer.dealer_code", read_only=True)
    dealer_mobile = serializers.CharField(source="dealer.mobile_number", read_only=True)
    assigned_rm_name = serializers.CharField(source="dealer.assigned_rm.full_name", read_only=True)
    campaign_name = serializers.CharField(source="campaign.campaign_name", read_only=True)
    time_slot_label = serializers.CharField(source="preferred_time_slot.display_label", read_only=True)

    class Meta:
        model = Confirmation
        fields = [
            "id",
            "dealer",
            "dealer_code",
            "dealer_mobile",
            "assigned_rm_name",
            "campaign",
            "campaign_name",
            "preferred_date",
            "preferred_time_slot",
            "time_slot_label",
            "submission_status",
            "submitted_at",
            "created_at",
        ]


class ManualBookingCreateSerializer(serializers.Serializer):
    dealer = serializers.PrimaryKeyRelatedField(queryset=Dealer.objects.all())
    campaign = serializers.PrimaryKeyRelatedField(queryset=Campaign.objects.all())
    preferred_date = serializers.DateField()
    preferred_time_slot = serializers.UUIDField()
    reason = serializers.CharField(required=False, allow_blank=True, default="Manual booking")


class RescheduleBookingSerializer(serializers.Serializer):
    preferred_date = serializers.DateField()
    preferred_time_slot = serializers.UUIDField()
    reason = serializers.CharField(required=False, allow_blank=True, default="")


class CancelBookingSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default="")


class BookingHistorySerializer(serializers.ModelSerializer):
    previous_slot_label = serializers.CharField(
        source="previous_time_slot.display_label", read_only=True, default=None
    )
    new_slot_label = serializers.CharField(
        source="new_time_slot.display_label", read_only=True, default=None
    )
    changed_by_name = serializers.CharField(
        source="changed_by.full_name", read_only=True, default="Dealer (Public)"
    )

    class Meta:
        model = ConfirmationHistory
        fields = [
            "id",
            "action",
            "previous_date",
            "previous_slot_label",
            "new_date",
            "new_slot_label",
            "reason",
            "changed_by_name",
            "created_at",
        ]
