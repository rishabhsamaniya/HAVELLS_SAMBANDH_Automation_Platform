from django.urls import path

from apps.scheduling.views import (
    BlockedSlotDeleteView,
    BlockedSlotListCreateView,
    BookingCancelView,
    BookingHistoryView,
    BookingListCreateView,
    BookingRescheduleView,
    HolidayDeleteView,
    HolidayListCreateView,
    InternalAvailabilityView,
    OperatingHoursConfigView,
    TimeSlotListCreateView,
    TimeSlotUpdateView,
)

urlpatterns = [
    path("config/", OperatingHoursConfigView.as_view(), name="scheduling-config"),
    path("slots/", TimeSlotListCreateView.as_view(), name="scheduling-slots"),
    path("slots/<uuid:pk>/", TimeSlotUpdateView.as_view(), name="scheduling-slot-update"),
    path("holidays/", HolidayListCreateView.as_view(), name="scheduling-holidays"),
    path("holidays/<uuid:pk>/", HolidayDeleteView.as_view(), name="scheduling-holiday-delete"),
    path("blocked-slots/", BlockedSlotListCreateView.as_view(), name="scheduling-blocked-slots"),
    path("blocked-slots/<uuid:pk>/", BlockedSlotDeleteView.as_view(), name="scheduling-blocked-slot-delete"),
    path("availability/", InternalAvailabilityView.as_view(), name="scheduling-availability"),
    path("bookings/", BookingListCreateView.as_view(), name="scheduling-bookings"),
    path("bookings/<uuid:pk>/reschedule/", BookingRescheduleView.as_view(), name="scheduling-booking-reschedule"),
    path("bookings/<uuid:pk>/cancel/", BookingCancelView.as_view(), name="scheduling-booking-cancel"),
    path("bookings/<uuid:pk>/history/", BookingHistoryView.as_view(), name="scheduling-booking-history"),
]
