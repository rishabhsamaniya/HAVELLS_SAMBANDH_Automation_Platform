"""Django Admin registration for custom mobile-based User model."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from apps.accounts.models import User


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("mobile_number", "full_name", "email", "reporting_manager")


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = (
            "mobile_number",
            "full_name",
            "email",
            "reporting_manager",
            "is_active",
            "is_staff",
            "is_superuser",
        )


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    list_display = (
        "full_name",
        "mobile_number",
        "email",
        "reporting_manager",
        "is_active",
        "is_staff",
        "last_login",
    )
    list_filter = ("is_active", "is_staff", "is_superuser")
    search_fields = ("full_name", "mobile_number", "email")
    ordering = ("-created_at",)
    readonly_fields = ("id", "last_login", "date_joined", "created_at", "updated_at")

    fieldsets = (
        ("Credentials", {"fields": ("mobile_number", "password")}),
        ("Personal Info", {"fields": ("full_name", "email", "reporting_manager")}),
        (
            "Access & Lockout",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "failed_login_attempts",
                    "locked_until",
                )
            },
        ),
        ("Timestamps", {"fields": ("id", "last_login", "date_joined", "created_at", "updated_at")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "mobile_number",
                    "full_name",
                    "email",
                    "reporting_manager",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                ),
            },
        ),
    )
