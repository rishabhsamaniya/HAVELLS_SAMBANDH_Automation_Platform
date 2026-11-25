from django.contrib import admin

from apps.permissions.models import Permission, RolePermission


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("codename", "name", "module", "action")
    list_filter = ("module", "action")
    search_fields = ("codename", "name", "module")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ("role", "permission", "created_at")
    list_filter = ("role", "permission__module")
    search_fields = ("role__name", "permission__codename")
    autocomplete_fields = ("role", "permission")
