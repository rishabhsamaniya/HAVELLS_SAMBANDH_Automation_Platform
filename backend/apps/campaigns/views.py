"""Views for Campaign Management."""
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.campaigns.models import Campaign
from apps.campaigns.selectors import get_campaigns_queryset
from apps.campaigns.serializers import CampaignSerializer
from apps.campaigns.services import create_campaign, update_campaign
from common.permissions.rbac import HasModulePermission
from common.responses.api import success_response


class CampaignListCreateView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    method_permissions = {
        "GET": "campaigns.view",
        "POST": ("campaigns.add", "campaigns.manage"),
    }
    serializer_class = CampaignSerializer
    search_fields = ["campaign_name", "campaign_code"]
    filterset_fields = ["status"]
    ordering_fields = ["start_date", "created_at"]

    def get_queryset(self):
        return get_campaigns_queryset()

    def post(self, request):
        serializer = CampaignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        campaign = create_campaign(actor=request.user, validated_data=serializer.validated_data)
        return success_response(
            data=CampaignSerializer(campaign).data,
            message="Campaign created successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class CampaignDetailUpdateView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    method_permissions = {
        "GET": "campaigns.view",
        "PATCH": ("campaigns.edit", "campaigns.manage"),
    }

    def get(self, request, pk):
        campaign = get_object_or_404(get_campaigns_queryset(), pk=pk)
        return success_response(data=CampaignSerializer(campaign).data)

    def patch(self, request, pk):
        campaign = get_object_or_404(Campaign, pk=pk)
        serializer = CampaignSerializer(campaign, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = update_campaign(
            actor=request.user,
            campaign=campaign,
            validated_data=serializer.validated_data,
        )
        return success_response(
            data=CampaignSerializer(updated).data,
            message="Campaign updated successfully.",
        )
