"""Views for Role Management & Role Permission Assignment."""
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.permissions.serializers import PermissionSerializer, RolePermissionsUpdateSerializer
from apps.permissions.services import assign_permissions_to_role
from apps.roles.models import Role
from apps.roles.selectors import get_roles_queryset
from apps.roles.serializers import RoleCreateSerializer, RoleSerializer, RoleUpdateSerializer
from apps.roles.services import create_role, update_role
from common.permissions.rbac import HasModulePermission
from common.responses.api import success_response


class RoleListCreateView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    method_permissions = {
        "GET": "roles.view",
        "POST": ("roles.add", "roles.manage"),
    }

    def get(self, request):
        qs = get_roles_queryset()
        return success_response(data=RoleSerializer(qs, many=True).data)

    def post(self, request):
        serializer = RoleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = create_role(actor=request.user, **serializer.validated_data)
        hydrated = get_roles_queryset().get(pk=role.pk)
        return success_response(
            data=RoleSerializer(hydrated).data,
            message="Role created successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class RoleDetailUpdateView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    method_permissions = {
        "GET": "roles.view",
        "PATCH": ("roles.edit", "roles.manage"),
    }

    def get(self, request, pk):
        role = get_object_or_404(get_roles_queryset(), pk=pk)
        return success_response(data=RoleSerializer(role).data)

    def patch(self, request, pk):
        role = get_object_or_404(Role, pk=pk)
        serializer = RoleUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        update_role(actor=request.user, role=role, validated_data=serializer.validated_data)
        hydrated = get_roles_queryset().get(pk=role.pk)
        return success_response(
            data=RoleSerializer(hydrated).data,
            message="Role updated successfully.",
        )


class RolePermissionAssignView(APIView):
    permission_classes = [IsAuthenticated, HasModulePermission]
    method_permissions = {
        "GET": ("roles.view", "permissions.view"),
        "POST": "permissions.manage",
    }

    def get(self, request, pk):
        role = get_object_or_404(get_roles_queryset(), pk=pk)
        perms = [rp.permission for rp in role.role_permissions.all()]
        return success_response(data=PermissionSerializer(perms, many=True).data)

    def post(self, request, pk):
        role = get_object_or_404(Role, pk=pk)
        serializer = RolePermissionsUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assign_permissions_to_role(
            actor=request.user,
            role=role,
            permission_ids=serializer.validated_data["permission_ids"],
        )
        hydrated = get_roles_queryset().get(pk=role.pk)
        return success_response(
            data=RoleSerializer(hydrated).data,
            message="Role permissions updated successfully.",
        )
