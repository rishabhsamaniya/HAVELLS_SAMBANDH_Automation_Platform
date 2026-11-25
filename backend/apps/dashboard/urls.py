from django.urls import path

from apps.dashboard.views import DashboardAnalyticsView, DashboardOverviewView

urlpatterns = [
    path("overview/", DashboardOverviewView.as_view(), name="dashboard-overview"),
    path("analytics/", DashboardAnalyticsView.as_view(), name="dashboard-analytics"),
]
