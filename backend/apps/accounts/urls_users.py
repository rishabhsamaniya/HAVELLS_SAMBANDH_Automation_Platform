from django.urls import path

from apps.accounts.views import (
    UserActivateView,
    UserActivityView,
    UserAdminResetPasswordView,
    UserDeactivateView,
    UserDetailUpdateView,
    UserListCreateView,
)

urlpatterns = [
    path("", UserListCreateView.as_view(), name="users-list-create"),
    path("<uuid:pk>/", UserDetailUpdateView.as_view(), name="users-detail-update"),
    path("<uuid:pk>/deactivate/", UserDeactivateView.as_view(), name="users-deactivate"),
    path("<uuid:pk>/activate/", UserActivateView.as_view(), name="users-activate"),
    path("<uuid:pk>/reset-password/", UserAdminResetPasswordView.as_view(), name="users-reset-password"),
    path("<uuid:pk>/activity/", UserActivityView.as_view(), name="users-activity"),
]
