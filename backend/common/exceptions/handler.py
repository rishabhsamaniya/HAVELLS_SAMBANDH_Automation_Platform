"""Production-safe DRF exception handler returning standardized envelopes."""
import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from .domain import DomainError

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    if isinstance(exc, DomainError):
        return Response(
            {
                "success": False,
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                },
            },
            status=exc.status_code,
        )

    response = exception_handler(exc, context)
    if response is not None:
        raw_data = response.data
        message = "Validation failed." if response.status_code == 400 else "Request failed."
        if isinstance(raw_data, dict):
            if "detail" in raw_data:
                message = str(raw_data["detail"])
            elif response.status_code == 400:
                # Surface the first specific field validation error in message for clear UX
                for field, errs in raw_data.items():
                    first_err = errs[0] if isinstance(errs, list) and errs else errs
                    label = field.replace("_", " ").capitalize()
                    message = f"{label}: {first_err}" if field != "non_field_errors" else str(first_err)
                    break
        response.data = {
            "success": False,
            "error": {
                "code": getattr(exc, "default_code", "API_ERROR").upper(),
                "message": message,
                "details": raw_data if isinstance(raw_data, dict) else {"non_field_errors": raw_data},
            },
        }
        return response

    # Never expose internal stack traces to API clients
    logger.exception("Unhandled API exception", exc_info=exc)
    return Response(
        {
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "details": {},
            },
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
