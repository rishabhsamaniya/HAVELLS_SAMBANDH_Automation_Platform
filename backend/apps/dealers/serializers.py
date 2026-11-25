"""Serializers for Dealer Management."""
from rest_framework import serializers

from apps.accounts.models import User
from apps.dealers.models import Dealer, DealerStatus
from common.validators.mobile import (
    normalize_dealer_code,
    normalize_indian_mobile,
    validate_indian_mobile,
)


class DealerSerializer(serializers.ModelSerializer):
    assigned_rm_name = serializers.CharField(source="assigned_rm.full_name", read_only=True)
    assigned_rm_mobile = serializers.CharField(source="assigned_rm.mobile_number", read_only=True)
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True, default=None)

    class Meta:
        model = Dealer
        fields = [
            "id",
            "dealer_code",
            "mobile_number",
            "status",
            "assigned_rm",
            "assigned_rm_name",
            "assigned_rm_mobile",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        ]


class DealerCreateSerializer(serializers.Serializer):
    dealer_code = serializers.CharField(max_length=64)
    mobile_number = serializers.CharField(max_length=20)
    assigned_rm = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(is_active=True))
    status = serializers.ChoiceField(choices=DealerStatus.choices, default=DealerStatus.ACTIVE)

    def validate_dealer_code(self, value: str) -> str:
        code = normalize_dealer_code(value)
        if not code:
            raise serializers.ValidationError("Dealer code is required.")
        if Dealer.objects.filter(dealer_code=code).exists():
            raise serializers.ValidationError("A dealer with this dealer code already exists.")
        return code

    def validate_mobile_number(self, value: str) -> str:
        normalized = normalize_indian_mobile(value)
        validate_indian_mobile(normalized)
        return normalized


class DealerUpdateSerializer(serializers.Serializer):
    dealer_code = serializers.CharField(max_length=64, required=False)
    mobile_number = serializers.CharField(max_length=20, required=False)
    assigned_rm = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True),
        required=False,
    )
    status = serializers.ChoiceField(choices=DealerStatus.choices, required=False)

    def validate_dealer_code(self, value: str) -> str:
        code = normalize_dealer_code(value)
        target = self.context.get("dealer")
        qs = Dealer.objects.filter(dealer_code=code)
        if target is not None:
            qs = qs.exclude(pk=target.pk)
        if qs.exists():
            raise serializers.ValidationError("A dealer with this dealer code already exists.")
        return code

    def validate_mobile_number(self, value: str) -> str:
        normalized = normalize_indian_mobile(value)
        validate_indian_mobile(normalized)
        return normalized
