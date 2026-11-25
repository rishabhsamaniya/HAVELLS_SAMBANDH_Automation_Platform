from django.urls import path

from apps.roles.views import (
    RoleDetailUpdateView,
    RoleListCreateView,
    RolePermissionAssignView,
)

urlpatterns = [
    path("", RoleListCreateView.as_view(), name="roles-list-create"),
    path("<uuid:pk>/", RoleDetailUpdateView.as_view(), name="roles-detail-update"),
    path("<uuid:pk>/permissions/", RolePermissionAssignView.as_view(), name="roles-permissions"),
]
