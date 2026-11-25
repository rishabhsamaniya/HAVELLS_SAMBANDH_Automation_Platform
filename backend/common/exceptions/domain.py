"""Custom domain exceptions for Havells Sambandh."""
from rest_framework import status


class DomainError(Exception):
    """Base domain exception translated into a safe API error response."""

    default_code = "DOMAIN_ERROR"
    default_message = "Unable to process the request."
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(
        self,
        message: str | None = None,
        code: str | None = None,
        status_code: int | None = None,
        details: dict | None = None,
    ) -> None:
        self.message = message or self.default_message
        self.code = code or self.default_code
        if status_code is not None:
            self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ConflictError(DomainError):
    default_code = "CONFLICT"
    status_code = status.HTTP_409_CONFLICT


class ForbiddenError(DomainError):
    default_code = "FORBIDDEN"
    default_message = "You do not have permission to perform this action."
    status_code = status.HTTP_403_FORBIDDEN


class NotFoundError(DomainError):
    default_code = "NOT_FOUND"
    default_message = "The requested resource was not found."
    status_code = status.HTTP_404_NOT_FOUND
