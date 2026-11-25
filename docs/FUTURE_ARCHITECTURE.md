# Future-Ready Architecture Review — Havells Sambandh (Phase 20)

| Field | Value |
| :--- | :--- |
| **Document Version** | 1.0.0 |
| **Phase** | Phase 20 — Future-Ready Architecture Review |
| **Scope** | Architectural readiness audit for post-v1.0 roadmap modules |

---

## Extensibility Audit Across All 15 Future-Scope Capabilities

| # | Future Capability | v1.0 Foundation & Extension Point | Breaking Changes Required? |
| :-: | :--- | :--- | :---: |
| 1 | **Multiple Dealer Engagement Campaigns** | `Campaign` model (`apps/campaigns`) is already a first-class FK on `ConfirmationLink` and `Confirmation`, with per-campaign `timezone` and lifecycle status. | None |
| 2 | **Multiple Experience Categories** | Add `apps/experiences` with `ExperienceCategory` linked to `Campaign`; keep public confirmation form schema driven by campaign template type. | None |
| 3 | **Experience Catalog** | Attach `ExperienceItem` models under `apps/experiences` referencing `ExperienceCategory` and `Campaign`. | None |
| 4 | **Experience Budget Management** | Add `apps/budgets` referencing `Campaign` and `User` (RM/Regional allocation) with ledger rows using UUID PKs and `AuditLog`. | None |
| 5 | **Dealer Reward Management** | Add `apps/rewards` referencing `Dealer`, `Campaign`, and `Confirmation` (triggering reward accrual via `on_form_submitted` hook). | None |
| 6 | **WhatsApp Business API Automation** | Implement `WhatsAppCloudProvider(BaseNotificationProvider)` in `apps/notifications/providers/` and register in `_PROVIDER_REGISTRY`. | None |
| 7 | **SMS Gateway Automation** | Implement `SMSGatewayProvider(BaseNotificationProvider)` in `apps/notifications/providers/` and dispatch via `send_notification_async` Celery task. | None |
| 8 | **Automated Reminders** | Add periodic Celery Beat task in `apps/notifications/tasks.py` querying pending `ConfirmationLink` records (`status__in=['active','shared']`) and dispatching WhatsApp/SMS reminders. | None |
| 9 | **Advanced RM Performance Tracking** | `apps/dashboard/selectors.py` and `apps/reports/selectors.py` already compute RM-level link/shared/confirmed/conversion aggregations cleanly decoupled from views. | None |
| 10 | **Advanced Analytics** | Extend `apps/dashboard/selectors.py` or attach materialized PostgreSQL views / read replicas without modifying REST contract envelopes. | None |
| 11 | **Multiple Business Units (BU)** | Add `BusinessUnit` FK to `User`, `Dealer`, and `Campaign`; extend `PermissionService.scope_dealer_queryset()` in one centralized location (`apps/permissions/services.py`). | Minimal additive migration |
| 12 | **Organization-Level Permissions** | `Permission` (`module.action`) and `RolePermission` are already database-driven and seeded idempotently; add scope-level permissions (e.g. `bu.view_all`) cleanly. | None |
| 13 | **Approval Workflows** | `confirmations.approve` permission already exists in `seed_rbac.py`; add a lightweight `ApprovalRequest` table linked via generic or FK references and `AuditLog`. | None |
| 14 | **AI-Based Reporting** | Report builders in `apps/reports/selectors.py` return structured `(headers, rows)` dictionaries that can feed LLM summarization/anomaly services directly without duplicating SQL/ORM logic. | None |
| 15 | **Automated MIS Reports** | Add a Celery Beat task invoking `REPORT_REGISTRY[key]` + `services/spreadsheet.py` and emailing `.xlsx` attachments via `LogEmailProvider` → SMTP provider. | None |
