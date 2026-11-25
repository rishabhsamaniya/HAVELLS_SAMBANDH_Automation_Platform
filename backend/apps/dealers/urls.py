from django.urls import path

from apps.dealers.views import (
    DealerConfirmationHistoryView,
    DealerDeactivateView,
    DealerDetailUpdateView,
    DealerExportView,
    DealerImportExcelView,
    DealerImportTemplateView,
    DealerListCreateView,
)

urlpatterns = [
    path("", DealerListCreateView.as_view(), name="dealers-list-create"),
    path("import/", DealerImportExcelView.as_view(), name="dealers-import"),
    path("import-template/", DealerImportTemplateView.as_view(), name="dealers-import-template"),
    path("export/", DealerExportView.as_view(), name="dealers-export"),
    path("<uuid:pk>/", DealerDetailUpdateView.as_view(), name="dealers-detail-update"),
    path("<uuid:pk>/deactivate/", DealerDeactivateView.as_view(), name="dealers-deactivate"),
    path("<uuid:pk>/confirmations/", DealerConfirmationHistoryView.as_view(), name="dealers-confirmations"),
]
