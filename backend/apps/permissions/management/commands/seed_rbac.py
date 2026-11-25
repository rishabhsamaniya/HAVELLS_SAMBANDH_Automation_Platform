"""Idempotent management command to seed roles, full permission catalog, and default RBAC mappings."""
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.permissions.models import Permission, PermissionAction, RolePermission
from apps.roles.models import Role

PERMISSION_CATALOG = [
    # Users
    ("users.view", "View Users", "users", PermissionAction.VIEW),
    ("users.add", "Add Users", "users", PermissionAction.ADD),
    ("users.edit", "Edit Users", "users", PermissionAction.EDIT),
    ("users.manage", "Manage User Lifecycle & Passwords", "users", PermissionAction.MANAGE),
    # Roles & Permissions
    ("roles.view", "View Roles", "roles", PermissionAction.VIEW),
    ("roles.add", "Create Roles", "roles", PermissionAction.ADD),
    ("roles.edit", "Edit Roles", "roles", PermissionAction.EDIT),
    ("roles.manage", "Manage Roles", "roles", PermissionAction.MANAGE),
    ("permissions.view", "View Permissions", "permissions", PermissionAction.VIEW),
    ("permissions.manage", "Assign Role Permissions", "permissions", PermissionAction.MANAGE),
    # Dealers
    ("dealers.view", "View Assigned Dealers", "dealers", PermissionAction.VIEW),
    ("dealers.view_all", "View All Organization Dealers", "dealers", PermissionAction.VIEW),
    ("dealers.add", "Add Dealers", "dealers", PermissionAction.ADD),
    ("dealers.edit", "Edit Dealers", "dealers", PermissionAction.EDIT),
    ("dealers.delete", "Deactivate Dealers", "dealers", PermissionAction.DELETE),
    ("dealers.import", "Import Dealers Excel", "dealers", PermissionAction.IMPORT),
    ("dealers.export", "Export Dealers Excel/CSV", "dealers", PermissionAction.EXPORT),
    # Campaigns
    ("campaigns.view", "View Campaigns", "campaigns", PermissionAction.VIEW),
    ("campaigns.add", "Create Campaigns", "campaigns", PermissionAction.ADD),
    ("campaigns.edit", "Edit Campaigns", "campaigns", PermissionAction.EDIT),
    ("campaigns.manage", "Manage Campaigns", "campaigns", PermissionAction.MANAGE),
    # Confirmation Links
    ("confirmation_links.view", "View Confirmation Links", "confirmation_links", PermissionAction.VIEW),
    ("confirmation_links.add", "Generate Confirmation Links", "confirmation_links", PermissionAction.ADD),
    ("confirmation_links.edit", "Update Confirmation Links", "confirmation_links", PermissionAction.EDIT),
    ("confirmation_links.delete", "Deactivate Confirmation Links", "confirmation_links", PermissionAction.DELETE),
    # Confirmations
    ("confirmations.view", "View Confirmations", "confirmations", PermissionAction.VIEW),
    ("confirmations.add", "Create Manual Confirmations", "confirmations", PermissionAction.ADD),
    ("confirmations.edit", "Reschedule or Cancel Confirmations", "confirmations", PermissionAction.EDIT),
    ("confirmations.approve", "Approve Confirmations", "confirmations", PermissionAction.APPROVE),
    # Scheduling
    ("scheduling.view", "View Schedules & Availability", "scheduling", PermissionAction.VIEW),
    ("scheduling.add", "Create Time Slots & Holidays", "scheduling", PermissionAction.ADD),
    ("scheduling.edit", "Edit Time Slots & Capacity", "scheduling", PermissionAction.EDIT),
    ("scheduling.manage", "Manage Scheduling Configuration", "scheduling", PermissionAction.MANAGE),
    # Dashboard & Reports
    ("dashboard.view", "View Dashboard & Analytics", "dashboard", PermissionAction.VIEW),
    ("reports.view", "View Reports", "reports", PermissionAction.VIEW),
    ("reports.export", "Export Reports Excel/CSV", "reports", PermissionAction.EXPORT),
    # Audit & Settings
    ("audit_logs.view", "View Audit Logs", "audit_logs", PermissionAction.VIEW),
    ("settings.manage", "Manage System Settings", "settings", PermissionAction.MANAGE),
]

DEFAULT_ROLE_PERMISSIONS = {
    "super_admin": [p[0] for p in PERMISSION_CATALOG],
    "admin": [
        "users.view", "users.add", "users.edit", "users.manage",
        "roles.view", "permissions.view",
        "dealers.view", "dealers.view_all", "dealers.add", "dealers.edit",
        "dealers.delete", "dealers.import", "dealers.export",
        "campaigns.view", "campaigns.add", "campaigns.edit", "campaigns.manage",
        "confirmation_links.view", "confirmation_links.add",
        "confirmation_links.edit", "confirmation_links.delete",
        "confirmations.view", "confirmations.add", "confirmations.edit", "confirmations.approve",
        "scheduling.view", "scheduling.add", "scheduling.edit", "scheduling.manage",
        "dashboard.view", "reports.view", "reports.export", "audit_logs.view",
    ],
    "management": [
        "dealers.view", "dealers.view_all", "dealers.export",
        "campaigns.view", "confirmation_links.view", "confirmations.view",
        "scheduling.view", "dashboard.view", "reports.view", "reports.export",
    ],
    "rm": [
        "dealers.view", "dealers.export",
        "campaigns.view",
        "confirmation_links.view", "confirmation_links.add",
        "confirmation_links.edit", "confirmation_links.delete",
        "confirmations.view", "confirmations.edit",
        "scheduling.view", "dashboard.view", "reports.view", "reports.export",
    ],
    "mis_executive": [
        "dealers.view", "dealers.view_all", "dealers.add", "dealers.edit",
        "dealers.import", "dealers.export",
        "campaigns.view", "confirmation_links.view", "confirmations.view",
        "scheduling.view", "dashboard.view", "reports.view", "reports.export",
    ],
}


class Command(BaseCommand):
    help = "Seed system roles, granular permission catalog, and default role-permission mappings."

    @transaction.atomic
    def handle(self, *args, **options):
        call_command("seed_roles", verbosity=0)

        perm_map = {}
        for codename, name, module, action in PERMISSION_CATALOG:
            perm, _ = Permission.objects.update_or_create(
                codename=codename,
                defaults={"name": name, "module": module, "action": action},
            )
            perm_map[codename] = perm

        for role_code, codenames in DEFAULT_ROLE_PERMISSIONS.items():
            role = Role.objects.get(code=role_code)
            for code in codenames:
                RolePermission.objects.get_or_create(role=role, permission=perm_map[code])

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(PERMISSION_CATALOG)} permissions across {len(DEFAULT_ROLE_PERMISSIONS)} system roles."
            )
        )
