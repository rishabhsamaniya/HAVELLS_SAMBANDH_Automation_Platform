"""Views for listing available RBAC permissions."""
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.permissions.selectors import get_permissions_queryset
from apps.permissions.serializers import PermissionSerializer
from common.permissions.rbac import HasModulePermission
from common.responses.api import success_response


class PermissionListView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    required_permission = "permissions.view"

    def get(self, request):
        qs = get_permissions_queryset()
        module = request.query_params.get("module")
        if module:
            qs = qs.filter(module=module)
        data = PermissionSerializer(qs, many=True).data
        return success_response(data=data)
