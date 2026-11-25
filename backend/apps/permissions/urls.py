from django.urls import path

from apps.permissions.views import PermissionListView

urlpatterns = [
    path("", PermissionListView.as_view(), name="permissions-list"),
]
