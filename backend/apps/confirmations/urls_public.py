from django.urls import path

from apps.confirmations.views_public import (
    PublicConfirmationAvailabilityView,
    PublicConfirmationDetailView,
    PublicConfirmationSubmitView,
)

urlpatterns = [
    path("<str:token>/", PublicConfirmationDetailView.as_view(), name="public-confirm-detail"),
    path(
        "<str:token>/availability/",
        PublicConfirmationAvailabilityView.as_view(),
        name="public-confirm-availability",
    ),
    path(
        "<str:token>/submit/",
        PublicConfirmationSubmitView.as_view(),
        name="public-confirm-submit",
    ),
]
