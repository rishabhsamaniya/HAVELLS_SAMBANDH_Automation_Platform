from django.urls import path

from apps.reports.views import (
    CampaignWiseReportView,
    ConfirmationReportView,
    DateWiseReportView,
    DealerMasterReportView,
    LinkUsageReportView,
    PendingDealerReportView,
    ReportExportView,
    RMPerformanceReportView,
    TimeSlotReportView,
)

urlpatterns = [
    path("dealer-master/", DealerMasterReportView.as_view(), name="reports-dealer-master"),
    path("confirmations/", ConfirmationReportView.as_view(), name="reports-confirmations"),
    path("pending/", PendingDealerReportView.as_view(), name="reports-pending"),
    path("rm-performance/", RMPerformanceReportView.as_view(), name="reports-rm-performance"),
    path("campaign-wise/", CampaignWiseReportView.as_view(), name="reports-campaign-wise"),
    path("date-wise/", DateWiseReportView.as_view(), name="reports-date-wise"),
    path("time-slot/", TimeSlotReportView.as_view(), name="reports-time-slot"),
    path("link-usage/", LinkUsageReportView.as_view(), name="reports-link-usage"),
    path("export/", ReportExportView.as_view(), name="reports-export"),
]
