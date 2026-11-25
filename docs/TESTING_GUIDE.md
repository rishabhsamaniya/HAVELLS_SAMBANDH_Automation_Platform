# Testing & Quality Assurance Guide — Havells Sambandh

| Field | Value |
| :--- | :--- |
| **Document Version** | 1.0.0 |
| **Phase** | Phase 17 — Testing & Quality Assurance |
| **Backend Runner** | Pytest + `pytest-django` + `pytest-cov` |
| **Frontend Runner** | Vitest + React Testing Library + `jsdom` |

---

## 1. Backend Test Suite (`backend/tests/`)

| Test File | Coverage Area |
| :--- | :--- |
| `test_auth_and_users.py` | Mobile login, `HttpOnly` refresh cookies, token rotation/blacklist, lockout (`423`), password change/reset, User CRUD, self-deactivation guard, `seed_roles` |
| `test_rbac.py` | Dynamic role creation, live permission assignment, `super_admin` protection, `PermissionService.scope_dealer_queryset` RM isolation |
| `test_dealers.py` | Dealer CRUD, duplicate code rejection, RM isolation on list/detail/export, `.xlsx` bulk import (row errors, zero overwrites) |
| `test_public_confirmation.py` | Same-month future-only date rule (`Asia/Kolkata`), last-day-of-month edge case, holidays, blocked slots, dealer/mobile validation, exact success message, duplicate & overbooking rejection (`409`), expired/deactivated/invalid tokens |
| `test_confirmation_links.py` | Cryptographic token hashing (zero raw token in DB/audit), auto-revoke prior unused links, mark-shared, deactivate, RM scope enforcement |
| `test_scheduling.py` | Operating hours, capacity updates, block/unblock slots, internal availability counts, manual booking, atomic reschedule & cancel with `ConfirmationHistory` |
| `test_dashboard.py` | Live 8 KPIs & 7 analytics datasets with Admin org-wide vs RM-scoped isolation |
| `test_reports.py` | All 8 standard reports, `.xlsx`/`.csv` export, `reports.export` RBAC, RM export isolation |
| `test_notifications_and_automation.py` | WhatsApp/SMS/Email/In-App provider interfaces, Celery `expire_overdue_confirmation_links` |
| `test_audit_logs.py` | Nested secret redaction (`password`, `token`, `refresh`), RBAC blocking, immutability (`405`) |
| `test_api_schema.py` | `/api/v1/health/`, OpenAPI 3.0 `/api/v1/schema/`, Swagger UI `/api/v1/docs/` |
| `test_security.py` | Security headers, `Cache-Control: no-store`, OOXML magic-byte upload check, formula-injection sanitization, stack-trace suppression |
| `test_e2e_workflow.py` | Full E2E flow: Admin Login → Create RM → Campaign → Dealer → Generate Link → Public Form Submit → Exact Success Message → Dashboard Update |

### Commands
```bash
cd backend
.venv/bin/pytest -v tests/
# With coverage report:
.venv/bin/pytest --cov=apps --cov=common --cov=services tests/
```

---

## 2. Frontend Test Suite (`frontend/src/`)

| Test File | Coverage Area |
| :--- | :--- |
| `features/auth/__tests__/LoginPage.test.tsx` | 10-digit Indian mobile validation & login form UX |
| `features/confirmations/__tests__/PublicConfirmationPage.test.tsx` | Strictly 4 fields only (no Dealer Name/Experience), same-month date & dynamic 1-hr slot selection, exact verbatim success screen, no-dates-remaining edge state |

### Commands
```bash
cd frontend
npm test
npm run typecheck
npm run build
```
