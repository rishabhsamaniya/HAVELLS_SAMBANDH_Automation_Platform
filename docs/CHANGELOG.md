# Changelog — Havells Sambandh

All notable changes to the **Havells Sambandh** platform are documented in this file.

## [1.0.0] — 2026-11-23
### Added
- **Phase 01–04:** Complete PRD, Feature List, Business Rules, Havells Red & White UI Rulebook, Component Library, 12-Screen Specifications, Modular Monolith Architecture, ER Diagram, and 15 UUID-based PostgreSQL Django models.
- **Phase 05:** Custom `User` model (`mobile_number` login), JWT access + `HttpOnly` rotating refresh cookies, lockout protection, password change/reset, User Management APIs, `seed_roles`, and React Login UI.
- **Phase 06:** Dynamic database-driven RBAC (`PermissionService`, `HasModulePermission`, 38 permissions across 5 roles via `seed_rbac`, Role & Permission Management APIs, `AdminLayout`, `PermissionGate`).
- **Phase 07:** Dealer Management CRUD, RM data isolation, validated `.xlsx` bulk import (row-level errors, zero overwrites), formula-safe Excel/CSV export, and React `DealersPage`.
- **Phase 08:** Highest-priority Public Dealer Date Confirmation Form (strictly 4 fields, same-month future-only `Asia/Kolkata` date rule, configurable 1-hour AM/PM slots, atomic `SELECT FOR UPDATE` booking, verbatim stakeholder success message, branded error/edge states).
- **Phase 09:** Campaign Management & Unique Confirmation Link Generation (256-bit cryptographic tokens, SHA-256 hash-only storage, one-time share URL & WhatsApp/SMS message, mark-shared, deactivate, auto-revoke).
- **Phase 10:** Scheduling Management (operating hours, slot capacity, holidays, block/unblock, availability matrix, manual booking, atomic RM/Admin reschedule & cancel with `ConfirmationHistory`).
- **Phase 11:** Real-time RBAC-scoped Admin Dashboard (8 KPIs + 7 Recharts analytics datasets).
- **Phase 12:** All 8 downloadable reports with multi-filters and formula-safe `.xlsx` / `.csv` exports.
- **Phase 13:** Pluggable Notification provider interfaces (WhatsApp, SMS, Email, In-App), 5 lifecycle automation hooks, and Celery Beat `expire_overdue_confirmation_links` task.
- **Phase 14:** Immutable RBAC-protected `/api/v1/audit-logs/` API with nested secret redaction and Frontend `SettingsPage` Audit Viewer.
- **Phase 15–17:** Complete OpenAPI 3.0 `/api/v1/docs/` & `API_DOCUMENTATION.md`, `SecurityHeadersMiddleware`, OOXML magic-byte upload check, 41 backend Pytest tests (incl. full E2E workflow), 3 React Vitest tests, and clean TypeScript/Vite production build.
- **Phase 18–20:** Render Blueprint (`render.yaml`), `Procfile`, `scripts/build_backend.sh`, `DEPLOYMENT_GUIDE.md`, complete `README.md`, and Future-Ready Architecture Review.
