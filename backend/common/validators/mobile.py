"""Validators for Indian mobile numbers and dealer codes."""
import re

from django.core.exceptions import ValidationError

INDIAN_MOBILE_REGEX = re.compile(r"^[6-9]\d{9}$")


def normalize_indian_mobile(value: str) -> str:
    """Strip whitespace, +91, or leading 0 to normalize a 10-digit Indian mobile number."""
    cleaned = re.sub(r"[\s\-()]", "", str(value or ""))
    if cleaned.startswith("+91") and len(cleaned) == 13:
        cleaned = cleaned[3:]
    elif cleaned.startswith("91") and len(cleaned) == 12:
        cleaned = cleaned[2:]
    elif cleaned.startswith("0") and len(cleaned) == 11:
        cleaned = cleaned[1:]
    return cleaned


def validate_indian_mobile(value: str) -> None:
    normalized = normalize_indian_mobile(value)
    if not INDIAN_MOBILE_REGEX.match(normalized):
        raise ValidationError(
            "Enter a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9."
        )


def normalize_dealer_code(value: str) -> str:
    return str(value or "").strip().upper()
