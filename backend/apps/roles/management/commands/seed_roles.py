"""Idempotent management command to seed the 5 initial Havells Sambandh roles."""
from django.core.management.base import BaseCommand

from apps.roles.models import Role

INITIAL_ROLES = [
    {
        "name": "Super Admin",
        "code": "super_admin",
        "description": "Full unrestricted system, RBAC, and configuration access.",
        "is_system_role": True,
    },
    {
        "name": "Admin",
        "code": "admin",
        "description": "Manages users, dealers, campaigns, confirmation links, schedules, and exports.",
        "is_system_role": True,
    },
    {
        "name": "Management",
        "code": "management",
        "description": "Organization-wide visibility into dashboards, analytics, and reports.",
        "is_system_role": True,
    },
    {
        "name": "RM",
        "code": "rm",
        "description": "Relationship Manager scoped strictly to assigned dealers and confirmations.",
        "is_system_role": True,
    },
    {
        "name": "MIS Executive",
        "code": "mis_executive",
        "description": "Manages authorized dealer records, Excel imports/exports, and operational reports.",
        "is_system_role": True,
    },
]


class Command(BaseCommand):
    help = "Seed the 5 initial system roles for Havells Sambandh."

    def handle(self, *args, **options):
        created_count = 0
        for role_data in INITIAL_ROLES:
            _, created = Role.objects.update_or_create(
                code=role_data["code"],
                defaults={
                    "name": role_data["name"],
                    "description": role_data["description"],
                    "is_system_role": role_data["is_system_role"],
                    "is_active": True,
                },
            )
            if created:
                created_count += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(INITIAL_ROLES)} system roles ({created_count} newly created)."
            )
        )
