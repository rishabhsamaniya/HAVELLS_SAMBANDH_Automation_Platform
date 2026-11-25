from django.urls import path

from apps.campaigns.views import CampaignDetailUpdateView, CampaignListCreateView

urlpatterns = [
    path("", CampaignListCreateView.as_view(), name="campaigns-list-create"),
    path("<uuid:pk>/", CampaignDetailUpdateView.as_view(), name="campaigns-detail-update"),
]
