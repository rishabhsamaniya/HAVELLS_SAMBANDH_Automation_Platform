# Dynamic RBAC Matrix — Havells Sambandh

| Field | Value |
| :--- | :--- |
| **Document Version** | 1.0.0 |
| **Phase** | Phase 06 — Dynamic Role-Based Access Control (RBAC) |
| **Enforcement Layer** | Backend `PermissionService` + DRF `HasModulePermission` + Queryset RM Isolation |
| **Resolution Rule** | Multi-role users receive the **union** of permissions across all active roles. Inactive roles grant zero permissions. |

---

## 1. Seeded Roles Overview

| Role Name | Code | Data Scope (Default) | Purpose |
| :--- | :--- | :--- | :--- |
| **Super Admin** | `super_admin` | Organization-wide (`*`) | Full unrestricted control across users, roles, permissions, settings, and audit logs. |
| **Admin** | `admin` | Organization-wide | Manages users, dealers, campaigns, confirmation links, schedules, dashboards, and exports. |
| **Management** | `management` | Organization-wide | Read-only dashboards, analytics, and report exports (write permissions configurable by Super Admin). |
| **RM** | `rm` | **Assigned dealers only** | Manages confirmation links, views schedules, and views/exports reports strictly for assigned dealers. |
| **MIS Executive** | `mis_executive` | Organization-wide (authorized dealer ops) | Manages dealer records, runs validated Excel imports/exports, and generates operational reports. |

---

## 2. Default Module × Action Permission Matrix

> Legend: `✓` = Granted by default · `—` = Denied by default (all grants are database-driven and dynamically configurable by Super Admin).

| Permission Codename | Module | Action | Super Admin | Admin | Management | RM | MIS Executive |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `users.view` | `users` | `view` | ✓ | ✓ | — | — | — |
| `users.add` | `users` | `add` | ✓ | ✓ | — | — | — |
| `users.edit` | `users` | `edit` | ✓ | ✓ | — | — | — |
| `users.manage` | `users` | `manage` | ✓ | ✓ | — | — | — |
| `roles.view` | `roles` | `view` | ✓ | ✓ | — | — | — |
| `roles.add` | `roles` | `add` | ✓ | — | — | — | — |
| `roles.edit` | `roles` | `edit` | ✓ | — | — | — | — |
| `roles.manage` | `roles` | `manage` | ✓ | — | — | — | — |
| `permissions.view` | `permissions` | `view` | ✓ | ✓ | — | — | — |
| `permissions.manage` | `permissions` | `manage` | ✓ | — | — | — | — |
| `dealers.view` | `dealers` | `view` | ✓ | ✓ | ✓ | ✓ (scoped) | ✓ |
| `dealers.view_all` | `dealers` | `view` | ✓ | ✓ | ✓ | — | ✓ |
| `dealers.add` | `dealers` | `add` | ✓ | ✓ | — | — | ✓ |
| `dealers.edit` | `dealers` | `edit` | ✓ | ✓ | — | — | ✓ |
| `dealers.delete` | `dealers` | `delete` | ✓ | ✓ | — | — | — |
| `dealers.import` | `dealers` | `import` | ✓ | ✓ | — | — | ✓ |
| `dealers.export` | `dealers` | `export` | ✓ | ✓ | ✓ | ✓ (scoped) | ✓ |
| `campaigns.view` | `campaigns` | `view` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `campaigns.add` | `campaigns` | `add` | ✓ | ✓ | — | — | — |
| `campaigns.edit` | `campaigns` | `edit` | ✓ | ✓ | — | — | — |
| `campaigns.manage` | `campaigns` | `manage` | ✓ | ✓ | — | — | — |
| `confirmation_links.view` | `confirmation_links` | `view` | ✓ | ✓ | ✓ | ✓ (scoped) | ✓ |
| `confirmation_links.add` | `confirmation_links` | `add` | ✓ | ✓ | — | ✓ (scoped) | — |
| `confirmation_links.edit` | `confirmation_links` | `edit` | ✓ | ✓ | — | ✓ (scoped) | — |
| `confirmation_links.delete` | `confirmation_links` | `delete` | ✓ | ✓ | — | ✓ (scoped) | — |
| `confirmations.view` | `confirmations` | `view` | ✓ | ✓ | ✓ | ✓ (scoped) | ✓ |
| `confirmations.add` | `confirmations` | `add` | ✓ | ✓ | — | — | — |
| `confirmations.edit` | `confirmations` | `edit` | ✓ | ✓ | — | ✓ (scoped) | — |
| `confirmations.approve` | `confirmations` | `approve` | ✓ | ✓ | — | — | — |
| `scheduling.view` | `scheduling` | `view` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `scheduling.add` | `scheduling` | `add` | ✓ | ✓ | — | — | — |
| `scheduling.edit` | `scheduling` | `edit` | ✓ | ✓ | — | — | — |
| `scheduling.manage` | `scheduling` | `manage` | ✓ | ✓ | — | — | — |
| `dashboard.view` | `dashboard` | `view` | ✓ | ✓ | ✓ | ✓ (scoped) | ✓ |
| `reports.view` | `reports` | `view` | ✓ | ✓ | ✓ | ✓ (scoped) | ✓ |
| `reports.export` | `reports` | `export` | ✓ | ✓ | ✓ | ✓ (scoped) | ✓ |
| `audit_logs.view` | `audit_logs` | `view` | ✓ | ✓ | — | — | — |
| `settings.manage` | `settings` | `manage` | ✓ | — | — | — | — |

---

## 3. Data Isolation Enforcement Rule

- Any user who does **not** hold `dealers.view_all` (and is not a Super Admin) is automatically restricted via `PermissionService.scope_dealer_queryset(user, queryset, rm_field=...)`:
  - `Dealer` queryset → filtered to `assigned_rm=user`
  - `ConfirmationLink` queryset → filtered to `assigned_rm=user`
  - `Confirmation` queryset → filtered to `dealer__assigned_rm=user`
  - Dashboard & Reports selectors → aggregated strictly over scoped records.
- Attempting to access or mutate another RM's dealer or link returns `403 Forbidden` or `404 Not Found`.
