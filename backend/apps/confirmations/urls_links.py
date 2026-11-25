from django.urls import path

from apps.confirmations.views_links import (
    ConfirmationLinkBulkGenerateView,
    ConfirmationLinkCopyShareView,
    ConfirmationLinkDeactivateView,
    ConfirmationLinkDetailView,
    ConfirmationLinkListCreateView,
    ConfirmationLinkMarkSharedView,
    ConfirmationLinkRegenerateView,
)

urlpatterns = [
    path("", ConfirmationLinkListCreateView.as_view(), name="confirmation-links-list-create"),
    path("bulk-generate/", ConfirmationLinkBulkGenerateView.as_view(), name="confirmation-links-bulk-generate"),
    path("<uuid:pk>/", ConfirmationLinkDetailView.as_view(), name="confirmation-links-detail"),
    path("<uuid:pk>/copy-share/", ConfirmationLinkCopyShareView.as_view(), name="confirmation-links-copy-share"),
    path("<uuid:pk>/regenerate/", ConfirmationLinkRegenerateView.as_view(), name="confirmation-links-regenerate"),
    path("<uuid:pk>/mark-shared/", ConfirmationLinkMarkSharedView.as_view(), name="confirmation-links-mark-shared"),
    path("<uuid:pk>/deactivate/", ConfirmationLinkDeactivateView.as_view(), name="confirmation-links-deactivate"),
]
