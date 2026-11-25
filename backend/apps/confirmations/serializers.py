"""Serializers for Public Dealer Date Confirmation Form (strictly 4 fields)."""
from rest_framework import serializers

from common.validators.mobile import normalize_indian_mobile, validate_indian_mobile


class PublicConfirmationSubmitSerializer(serializers.Serializer):
    """Strict 4-field public dealer confirmation payload."""

    dealer_code = serializers.CharField(max_length=64)
    mobile_number = serializers.CharField(max_length=20)
    preferred_date = serializers.DateField()
    preferred_time_slot = serializers.UUIDField()

    def validate_mobile_number(self, value: str) -> str:
        normalized = normalize_indian_mobile(value)
        validate_indian_mobile(normalized)
        return normalized
