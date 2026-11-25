"""Public (zero-login, token-authorized) views for Dealer Date Confirmation."""
from datetime import date

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.confirmations.serializers import PublicConfirmationSubmitSerializer
from apps.confirmations.services import (
    APPROVED_SUCCESS_MESSAGE,
    get_public_date_availability,
    get_public_link_metadata,
    submit_public_confirmation,
)
from common.exceptions.domain import DomainError
from common.responses.api import success_response


class PublicConfirmationDetailView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = "public_confirm_read"

    def get(self, request, token: str):
        data = get_public_link_metadata(raw_token=token)
        return success_response(data=data)


class PublicConfirmationAvailabilityView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = "public_confirm_read"

    def get(self, request, token: str):
        raw_date = request.query_params.get("date")
        if not raw_date:
            raise DomainError(
                message="Query parameter 'date' (YYYY-MM-DD) is required.",
                code="DATE_REQUIRED",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        try:
            parsed_date = date.fromisoformat(raw_date)
        except ValueError as exc:
            raise DomainError(
                message="Invalid date format. Expected YYYY-MM-DD.",
                code="INVALID_DATE",
                status_code=status.HTTP_400_BAD_REQUEST,
            ) from exc

        data = get_public_date_availability(raw_token=token, target_date=parsed_date)
        return success_response(data=data)


class PublicConfirmationSubmitView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = "public_confirm_submit"

    def post(self, request, token: str):
        serializer = PublicConfirmationSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = submit_public_confirmation(
            raw_token=token,
            dealer_code=serializer.validated_data["dealer_code"],
            mobile_number=serializer.validated_data["mobile_number"],
            preferred_date=serializer.validated_data["preferred_date"],
            preferred_time_slot_id=serializer.validated_data["preferred_time_slot"],
        )
        return success_response(
            data=result,
            message=APPROVED_SUCCESS_MESSAGE,
            status_code=status.HTTP_201_CREATED,
        )
