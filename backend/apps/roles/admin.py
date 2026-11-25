from django.contrib import admin

from apps.roles.models import Role, UserRole


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_system_role", "is_active", "created_at")
    list_filter = ("is_system_role", "is_active")
    search_fields = ("name", "code")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "assigned_by", "assigned_at")
    list_filter = ("role",)
    search_fields = ("user__full_name", "user__mobile_number", "role__name")
    autocomplete_fields = ("user", "role", "assigned_by")
