"""Views for Scheduling Management (Config, Slots, Holidays, Blocked Slots, Availability, Bookings)."""
from datetime import date

from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.audit_logs.services import log_audit_event
from apps.confirmations.selectors import get_scoped_confirmations_queryset
from apps.scheduling.models import BlockedSlot, Holiday, OperatingHoursConfig, TimeSlot
from apps.scheduling.serializers import (
    BlockedSlotSerializer,
    BookingHistorySerializer,
    BookingSerializer,
    CancelBookingSerializer,
    HolidaySerializer,
    ManualBookingCreateSerializer,
    OperatingHoursConfigSerializer,
    RescheduleBookingSerializer,
    TimeSlotSerializer,
)
from apps.scheduling.services import (
    cancel_booking,
    create_manual_booking,
    generate_time_slots_from_config,
    get_internal_date_availability,
    reschedule_booking,
    update_operating_hours,
)
from common.exceptions.domain import DomainError
from common.permissions.rbac import HasModulePermission
from common.responses.api import success_response


class OperatingHoursConfigView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    method_permissions = {
        "GET": "scheduling.view",
        "POST": "scheduling.manage",
    }

    def get(self, request):
        config = OperatingHoursConfig.objects.filter(is_active=True).first()
        if config is None:
            generate_time_slots_from_config()
            config = OperatingHoursConfig.objects.filter(is_active=True).first()
        return success_response(data=OperatingHoursConfigSerializer(config).data)

    def post(self, request):
        serializer = OperatingHoursConfigSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        config = update_operating_hours(actor=request.user, validated_data=serializer.validated_data)
        return success_response(
            data=OperatingHoursConfigSerializer(config).data,
            message="Operating hours updated and time slots synchronized.",
        )


class TimeSlotListCreateView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    method_permissions = {
        "GET": "scheduling.view",
        "POST": ("scheduling.add", "scheduling.manage"),
    }

    def get(self, request):
        slots = TimeSlot.objects.all().order_by("start_time")
        return success_response(data=TimeSlotSerializer(slots, many=True).data)

    def post(self, request):
        serializer = TimeSlotSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        slot = serializer.save()
        log_audit_event(
            user=request.user,
            action="TIME_SLOT_CREATED",
            module="scheduling",
            object_type="TimeSlot",
            object_id=str(slot.id),
            new_values={"label": slot.display_label, "max_capacity": slot.max_capacity},
        )
        return success_response(
            data=TimeSlotSerializer(slot).data,
            message="Time slot created successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class TimeSlotUpdateView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    required_permission = ("scheduling.edit", "scheduling.manage")

    def patch(self, request, pk):
        slot = get_object_or_404(TimeSlot, pk=pk)
        old_vals = {"max_capacity": slot.max_capacity, "is_active": slot.is_active}
        serializer = TimeSlotSerializer(slot, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        log_audit_event(
            user=request.user,
            action="TIME_SLOT_UPDATED",
            module="scheduling",
            object_type="TimeSlot",
            object_id=str(updated.id),
            old_values=old_vals,
            new_values={"max_capacity": updated.max_capacity, "is_active": updated.is_active},
        )
        return success_response(
            data=TimeSlotSerializer(updated).data,
            message="Time slot updated successfully.",
        )


class HolidayListCreateView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    method_permissions = {
        "GET": "scheduling.view",
        "POST": ("scheduling.add", "scheduling.manage"),
    }

    def get(self, request):
        holidays = Holiday.objects.filter(is_active=True).order_by("date")
        return success_response(data=HolidaySerializer(holidays, many=True).data)

    def post(self, request):
        serializer = HolidaySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        holiday = serializer.save(created_by=request.user)
        log_audit_event(
            user=request.user,
            action="HOLIDAY_CREATED",
            module="scheduling",
            object_type="Holiday",
            object_id=str(holiday.id),
            new_values={"date": holiday.date.isoformat(), "name": holiday.name},
        )
        return success_response(
            data=HolidaySerializer(holiday).data,
            message="Holiday added successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class HolidayDeleteView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    required_permission = "scheduling.manage"

    def delete(self, request, pk):
        holiday = get_object_or_404(Holiday, pk=pk)
        holiday.delete()
        return success_response(message="Holiday removed successfully.")


class BlockedSlotListCreateView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    method_permissions = {
        "GET": "scheduling.view",
        "POST": ("scheduling.edit", "scheduling.manage"),
    }

    def get(self, request):
        qs = BlockedSlot.objects.select_related("time_slot").filter(is_active=True)
        date_param = request.query_params.get("date")
        if date_param:
            qs = qs.filter(date=date_param)
        return success_response(data=BlockedSlotSerializer(qs, many=True).data)

    def post(self, request):
        serializer = BlockedSlotSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        blocked = serializer.save(created_by=request.user)
        log_audit_event(
            user=request.user,
            action="SLOT_BLOCKED",
            module="scheduling",
            object_type="BlockedSlot",
            object_id=str(blocked.id),
            new_values={"date": blocked.date.isoformat(), "slot": blocked.time_slot.display_label},
        )
        return success_response(
            data=BlockedSlotSerializer(blocked).data,
            message="Time slot blocked successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class BlockedSlotDeleteView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    required_permission = ("scheduling.edit", "scheduling.manage")

    def delete(self, request, pk):
        blocked = get_object_or_404(BlockedSlot, pk=pk)
        blocked.delete()
        log_audit_event(
            user=request.user,
            action="SLOT_UNBLOCKED",
            module="scheduling",
            object_type="BlockedSlot",
            object_id=str(pk),
        )
        return success_response(message="Time slot unblocked successfully.")


class InternalAvailabilityView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    required_permission = "scheduling.view"

    def get(self, request):
        raw_date = request.query_params.get("date")
        if not raw_date:
            raise DomainError("Query parameter 'date' (YYYY-MM-DD) is required.", code="DATE_REQUIRED")
        try:
            target_date = date.fromisoformat(raw_date)
        except ValueError as exc:
            raise DomainError("Invalid date format. Expected YYYY-MM-DD.", code="INVALID_DATE") from exc
        return success_response(data=get_internal_date_availability(target_date=target_date))


class BookingListCreateView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    method_permissions = {
        "GET": "confirmations.view",
        "POST": "confirmations.add",
    }
    serializer_class = BookingSerializer
    filterset_fields = ["campaign", "preferred_date", "preferred_time_slot", "submission_status"]
    search_fields = ["dealer__dealer_code", "dealer__mobile_number"]

    def get_queryset(self):
        return get_scoped_confirmations_queryset(self.request.user)

    def post(self, request):
        serializer = ManualBookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = create_manual_booking(
            actor=request.user,
            dealer=serializer.validated_data["dealer"],
            campaign=serializer.validated_data["campaign"],
            preferred_date=serializer.validated_data["preferred_date"],
            preferred_time_slot_id=serializer.validated_data["preferred_time_slot"],
            reason=serializer.validated_data.get("reason", ""),
        )
        return success_response(
            data=BookingSerializer(booking).data,
            message="Manual booking created successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class BookingRescheduleView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    required_permission = "confirmations.edit"

    def post(self, request, pk):
        confirmation = get_object_or_404(get_scoped_confirmations_queryset(request.user), pk=pk)
        serializer = RescheduleBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = reschedule_booking(
            actor=request.user,
            confirmation=confirmation,
            new_date=serializer.validated_data["preferred_date"],
            new_time_slot_id=serializer.validated_data["preferred_time_slot"],
            reason=serializer.validated_data.get("reason", ""),
        )
        return success_response(
            data=BookingSerializer(updated).data,
            message="Booking rescheduled successfully.",
        )


class BookingCancelView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    required_permission = "confirmations.edit"

    def post(self, request, pk):
        confirmation = get_object_or_404(get_scoped_confirmations_queryset(request.user), pk=pk)
        serializer = CancelBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = cancel_booking(
            actor=request.user,
            confirmation=confirmation,
            reason=serializer.validated_data.get("reason", ""),
        )
        return success_response(
            data=BookingSerializer(updated).data,
            message="Booking cancelled successfully.",
        )


class BookingHistoryView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    required_permission = "confirmations.view"

    def get(self, request, pk):
        confirmation = get_object_or_404(get_scoped_confirmations_queryset(request.user), pk=pk)
        history = confirmation.history.select_related(
            "previous_time_slot", "new_time_slot", "changed_by"
        ).all()
        return success_response(data=BookingHistorySerializer(history, many=True).data)
