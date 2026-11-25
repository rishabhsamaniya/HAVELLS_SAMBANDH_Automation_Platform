"""Views for internal Confirmation Link Management: Single, Bulk Generate, Copy-Share & Regenerate."""
from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.campaigns.models import Campaign
from apps.confirmations.models import ConfirmationLink, ConfirmationLinkStatus
from apps.confirmations.selectors import get_scoped_confirmation_links_queryset
from apps.confirmations.services_links import (
    bulk_generate_confirmation_links,
    deactivate_confirmation_link,
    generate_confirmation_link,
    get_copyable_link_and_mark_shared,
    mark_confirmation_link_shared,
    regenerate_confirmation_link,
)
from apps.dealers.models import Dealer
from common.permissions.rbac import HasModulePermission
from common.responses.api import success_response


class ConfirmationLinkSerializer(serializers.ModelSerializer):
    dealer_code = serializers.CharField(source="dealer.dealer_code", read_only=True)
    dealer_mobile = serializers.CharField(source="dealer.mobile_number", read_only=True)
    campaign_name = serializers.CharField(source="campaign.campaign_name", read_only=True)
    assigned_rm_name = serializers.CharField(source="assigned_rm.full_name", read_only=True)
    can_copy = serializers.SerializerMethodField()
    can_regenerate = serializers.SerializerMethodField()

    class Meta:
        model = ConfirmationLink
        fields = [
            "id",
            "dealer",
            "dealer_code",
            "dealer_mobile",
            "campaign",
            "campaign_name",
            "assigned_rm",
            "assigned_rm_name",
            "allowed_month",
            "status",
            "shared_at",
            "expires_at",
            "max_submissions",
            "submission_count",
            "is_regenerated",
            "regeneration_count",
            "can_copy",
            "can_regenerate",
            "created_at",
        ]

    def get_can_copy(self, obj: ConfirmationLink) -> bool:
        return (
            obj.status in (ConfirmationLinkStatus.ACTIVE, ConfirmationLinkStatus.SHARED)
            and not obj.is_expired
            and bool(obj.encrypted_token)
        )

    def get_can_regenerate(self, obj: ConfirmationLink) -> bool:
        return obj.status != ConfirmationLinkStatus.USED


class ConfirmationLinkCreateSerializer(serializers.Serializer):
    dealer = serializers.PrimaryKeyRelatedField(queryset=Dealer.objects.all())
    campaign = serializers.PrimaryKeyRelatedField(queryset=Campaign.objects.all())
    expires_at = serializers.DateTimeField(required=False, allow_null=True)
    max_submissions = serializers.IntegerField(required=False, default=1, min_value=1, max_value=10)


class BulkConfirmationLinkCreateSerializer(serializers.Serializer):
    campaign = serializers.PrimaryKeyRelatedField(queryset=Campaign.objects.all())
    dealer_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=list,
    )
    select_all_active = serializers.BooleanField(required=False, default=False)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)


class ConfirmationLinkListCreateView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    method_permissions = {
        "GET": "confirmation_links.view",
        "POST": "confirmation_links.add",
    }
    serializer_class = ConfirmationLinkSerializer
    search_fields = ["dealer__dealer_code", "dealer__mobile_number"]
    filterset_fields = ["dealer", "campaign", "assigned_rm", "status", "allowed_month", "is_regenerated"]
    ordering_fields = ["created_at", "expires_at", "shared_at"]

    def get_queryset(self):
        return get_scoped_confirmation_links_queryset(self.request.user)

    def post(self, request):
        serializer = ConfirmationLinkCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = generate_confirmation_link(
            actor=request.user,
            dealer=serializer.validated_data["dealer"],
            campaign=serializer.validated_data["campaign"],
            expires_at=serializer.validated_data.get("expires_at"),
            max_submissions=serializer.validated_data.get("max_submissions", 1),
        )
        payload = ConfirmationLinkSerializer(result["link"]).data
        payload["shareable_url"] = result["shareable_url"]
        payload["share_message"] = result["share_message"]
        return success_response(
            data=payload,
            message="Confirmation link generated successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class ConfirmationLinkBulkGenerateView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    required_permission = "confirmation_links.add"

    def post(self, request):
        serializer = BulkConfirmationLinkCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = bulk_generate_confirmation_links(
            actor=request.user,
            campaign=serializer.validated_data["campaign"],
            dealer_ids=serializer.validated_data.get("dealer_ids"),
            select_all_active=serializer.validated_data.get("select_all_active", False),
            expires_at=serializer.validated_data.get("expires_at"),
        )
        created_serialized = []
        for item in result["created_links"]:
            row = ConfirmationLinkSerializer(item["link"]).data
            row["shareable_url"] = item["shareable_url"]
            row["share_message"] = item["share_message"]
            created_serialized.append(row)

        return success_response(
            data={
                "created_count": result["created_count"],
                "skipped_count": result["skipped_count"],
                "links": created_serialized,
                "skipped": result["skipped"],
            },
            message=f"Bulk generation completed: {result['created_count']} created, {result['skipped_count']} skipped.",
            status_code=status.HTTP_201_CREATED,
        )


class ConfirmationLinkDetailView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    required_permission = "confirmation_links.view"

    def get(self, request, pk):
        link = get_object_or_404(get_scoped_confirmation_links_queryset(request.user), pk=pk)
        return success_response(data=ConfirmationLinkSerializer(link).data)


class ConfirmationLinkCopyShareView(APIView):
    """Retrieve copyable URL/message anytime & automatically mark link as shared."""

    permission_classes = [IsAuthenticated, HasModulePermission]
    required_permission = "confirmation_links.view"

    def post(self, request, pk):
        link = get_object_or_404(get_scoped_confirmation_links_queryset(request.user), pk=pk)
        result = get_copyable_link_and_mark_shared(actor=request.user, link=link)
        payload = ConfirmationLinkSerializer(result["link"]).data
        payload["shareable_url"] = result["shareable_url"]
        payload["share_message"] = result["share_message"]
        return success_response(
            data=payload,
            message="Link ready to share and counted in Links Shared.",
        )


class ConfirmationLinkRegenerateView(APIView):
    """Regenerate a fresh link for the same dealer+campaign and track regeneration KPIs."""

    permission_classes = [IsAuthenticated, HasModulePermission]
    required_permission = ("confirmation_links.add", "confirmation_links.edit")

    def post(self, request, pk):
        existing = get_object_or_404(get_scoped_confirmation_links_queryset(request.user), pk=pk)
        result = regenerate_confirmation_link(actor=request.user, existing_link=existing)
        payload = ConfirmationLinkSerializer(result["link"]).data
        payload["shareable_url"] = result["shareable_url"]
        payload["share_message"] = result["share_message"]
        return success_response(
            data=payload,
            message="Confirmation link regenerated successfully.",
            status_code=status.HTTP_200_OK,
        )


class ConfirmationLinkMarkSharedView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    required_permission = "confirmation_links.edit"

    def post(self, request, pk):
        link = get_object_or_404(get_scoped_confirmation_links_queryset(request.user), pk=pk)
        updated = mark_confirmation_link_shared(actor=request.user, link=link)
        return success_response(
            data=ConfirmationLinkSerializer(updated).data,
            message="Confirmation link marked as shared.",
        )


class ConfirmationLinkDeactivateView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    required_permission = "confirmation_links.delete"

    def post(self, request, pk):
        link = get_object_or_404(get_scoped_confirmation_links_queryset(request.user), pk=pk)
        updated = deactivate_confirmation_link(actor=request.user, link=link)
        return success_response(
            data=ConfirmationLinkSerializer(updated).data,
            message="Confirmation link deactivated.",
        )
