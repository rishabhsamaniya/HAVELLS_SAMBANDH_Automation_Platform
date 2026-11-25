# Product Requirement Document (PRD)
# Havells Sambandh — Enterprise Dealer Engagement & Automation Platform

| Field | Value |
| :--- | :--- |
| **Document Version** | 1.0.0 |
| **Status** | Phase 01 — Draft for Approval |
| **Project Name** | Havells Sambandh |
| **Initial Module** | Dealer Date Confirmation System (v1.0) |
| **Target Stack** | Django 5+ / DRF, React + TypeScript + Tailwind CSS, PostgreSQL, Celery + Redis |
| **Default Timezone** | `Asia/Kolkata` (IST, UTC+05:30) |
| **Last Updated** | 2026-11-23 |

---

## 1. Product Overview

**Havells Sambandh** is an enterprise-grade Dealer Engagement & Experience Management Platform built for Havells' internal channel management, sales operations, and MIS teams. The platform centralizes dealer records, automates personalized dealer outreach via cryptographically secure confirmation links, enforces strict scheduling and capacity rules, provides real-time operational visibility through role-scoped dashboards, and generates permission-controlled analytical reports.

The **v1.0 release** delivers the **Dealer Date Confirmation System** — enabling internal Relationship Managers (RMs) and Administrators to share unique, token-protected confirmation links with authorized dealers so dealers can confirm their preferred engagement date and one-hour time slot without requiring an account or login.

The underlying platform is architected as a modular, API-first system designed to scale cleanly into future engagement campaigns, experience catalogs, reward management, omnichannel messaging automation (WhatsApp Business API, SMS, Email), and multi-business-unit governance.

---

## 2. Business Objectives

| ID | Objective | Measurable Outcome |
| :--- | :--- | :--- |
| **BO-01** | Eliminate manual date/time coordination via phone calls, ad-hoc spreadsheets, and WhatsApp follow-ups | ≥ 90% of dealer confirmations captured directly through personalized links |
| **BO-02** | Prevent scheduling conflicts, double bookings, and out-of-window date selections | 0 over-capacity bookings and 0 out-of-month submissions (100% backend enforcement) |
| **BO-03** | Enforce strict organizational data governance and RM territory isolation | 100% of API endpoints enforce dynamic RBAC and queryset-level RM scoping |
| **BO-04** | Provide real-time visibility into dealer outreach, pending confirmations, and RM performance | Live dashboard KPIs and one-click Excel/CSV exports derived directly from PostgreSQL |
| **BO-05** | Establish a tamper-evident audit trail for compliance and operational accountability | 100% of critical mutations logged with actor, before/after state, timestamp, and IP |
| **BO-06** | Create an extensible foundation for future Havells dealer engagement programs | Modular Django apps and provider-abstracted notification/automation services |

---

## 3. Target Users

### 3.1 Internal Users (Authenticated via Mobile Number + Password)
1. **Super Admin** — Platform owner with unrestricted system, security, RBAC, and configuration control.
2. **Admin** — Operations lead managing users, dealers, campaigns, confirmation links, schedules, and reports.
3. **Management** — Leadership stakeholders monitoring organization-wide KPIs, campaign performance, and RM metrics.
4. **RM (Relationship Manager)** — Field/channel managers handling their assigned dealer portfolio, generating/sharing links, and monitoring confirmations.
5. **MIS Executive** — Data operations specialists handling bulk Excel imports/exports, data validation, and operational reporting.

### 3.2 External Users (Unauthenticated, Token-Authorized)
6. **Havells Dealer** — Registered channel partner who receives a unique confirmation link from their RM/Admin and submits their preferred date and time slot on a mobile-first, friction-free public form.

---

## 4. User Personas

| Persona | Role | Primary Goals | Key Pain Points | Primary Modules Used |
| :--- | :--- | :--- | :--- | :--- |
| **Vikram Mehta** | Super Admin (IT / Platform Admin) | Maintain platform security, manage roles/permissions dynamically, monitor audit logs, configure global scheduling defaults | Hardcoded permissions, lack of audit trail, manual DB interventions | Auth, Users, Roles & Permissions, Scheduling Config, Audit Logs |
| **Ananya Sharma** | Admin (Channel Operations Manager) | Onboard dealers, launch monthly campaigns, manage schedules/holidays, resolve rescheduling requests, export master reports | Overbooked time slots, duplicate dealer entries, delayed status updates from field RMs | Dashboard, Dealers, Campaigns, Links, Scheduling, Reports |
| **Rajesh Kapoor** | Management (VP / Regional Head) | Track overall confirmation rate, compare RM and campaign performance, identify bottlenecks early | Consolidated Excel sheets arriving days late with inconsistent numbers | Dashboard, Analytics, Reports (Read-Only by default) |
| **Suresh Nair** | RM (Relationship Manager) | Quickly generate and share links via WhatsApp/SMS to his dealers, see who is pending, assist dealers needing rescheduling | Losing track of which dealer confirmed; accidentally seeing or editing another RM's dealers | Dashboard (Scoped), Dealers (Assigned), Confirmation Links, Schedule View, Reports (Scoped) |
| **Priya Verma** | MIS Executive | Bulk-import dealer lists cleanly without overwriting valid data, validate records, generate daily/monthly Excel reports | Dirty Excel uploads breaking records, manual reconciliation of confirmed vs. pending dealers | Dealers (Import/Export), Reports, Confirmation Tracking |
| **Ramesh Gupta** | Havells Dealer (External) | Confirm a convenient date and 1-hour slot in under 60 seconds on a mobile phone without creating an account | Complex login flows, confusing forms, selecting a slot that turns out to be unavailable | Public Dealer Date Confirmation Form |

---

## 5. Business Requirements

1. **BR-01 (Mobile-First Authentication):** Internal users authenticate using a unique 10-digit Indian mobile number and password, backed by JWT authentication with refresh rotation and account lockout protection.
2. **BR-02 (Dynamic RBAC):** All roles and permissions must be database-driven and dynamically configurable by authorized administrators without code deployments. Frontend visibility must never be treated as a security boundary.
3. **BR-03 (Strict RM Data Isolation):** Relationship Managers must only view and operate on dealers explicitly assigned to them unless granted broader organizational permission.
4. **BR-04 (Zero-Login Dealer Experience):** Dealers must never be required to create an account or log in to confirm their date and time. Access is governed strictly by a cryptographically secure, single-dealer confirmation link.
5. **BR-05 (Minimalist Public Form):** The public Date Confirmation Form must collect **only** four fields: `Dealer Code`, `Mobile Number`, `Preferred Date`, and `Preferred Time Slot`. No dealer name, experience, email, address, or extra PII may be requested on the public form.
6. **BR-06 (Same-Month Future-Only Date Window):** Dealers may only select strictly future dates within the exact calendar month in which their confirmation link was generated/shared (`allowed_month`), evaluated against the backend's authoritative clock in the campaign timezone (`Asia/Kolkata` default).
7. **BR-07 (Configurable One-Hour Slot Engine):** Time slots are generated dynamically from admin-configurable operating hours (default 60-minute duration, default capacity 1 dealer per slot) and displayed in readable AM/PM format.
8. **BR-08 (Concurrency-Safe Capacity Enforcement):** Simultaneous booking attempts for the same date and time slot must be serialized via atomic PostgreSQL transactions and row-level locking to guarantee zero overbooking.
9. **BR-09 (Immutable Dealer Submission):** Once submitted, a dealer cannot self-edit their confirmation. Changes require an authorized RM or Admin rescheduling/cancellation workflow.
10. **BR-10 (Safe Bulk Excel Operations):** Dealer Excel imports must validate schema, detect duplicates, never silently overwrite existing records, and return granular row-level error summaries.
11. **BR-11 (Enterprise Observability & Auditability):** Every sensitive action (user/role changes, dealer imports, link generation/deactivation, confirmation submission, rescheduling, report exports) must be recorded in an immutable audit log without leaking secrets or raw tokens.

---

## 6. Functional Requirements

### 6.1 Module Map & Dependencies

| Module ID | Module Name | Backend App | Depends On | Release |
| :--- | :--- | :--- | :--- | :--- |
| **M01** | Authentication & User Management | `apps/accounts` | Core DB | v1.0 |
| **M02** | Dynamic RBAC (Roles & Permissions) | `apps/roles`, `apps/permissions` | M01 | v1.0 |
| **M03** | Dealer Management & Excel Import/Export | `apps/dealers` | M01, M02 | v1.0 |
| **M04** | Campaign Management | `apps/campaigns` | M01, M02 | v1.0 |
| **M05** | Scheduling Engine (Slots, Holidays, Capacity) | `apps/scheduling` | M01, M02 | v1.0 |
| **M06** | Unique Confirmation Link Management | `apps/confirmations` | M01, M02, M03, M04 | v1.0 |
| **M07** | Public Dealer Date Confirmation Form | `apps/confirmations` (public API) | M03, M04, M05, M06 | v1.0 |
| **M08** | Admin Dashboard & Analytics | `apps/dashboard` | M02, M03, M04, M05, M06, M07 | v1.0 |
| **M09** | Reporting & Excel/CSV Export | `apps/reports` | M02, M03, M04, M05, M06, M07 | v1.0 |
| **M10** | Notifications & Automation Hooks | `apps/notifications` | M06, M07, Celery/Redis | v1.0 (interface + events) |
| **M11** | Audit Logging | `apps/audit_logs` | M01–M10 | v1.0 |

### 6.2 Core Functional Requirements Summary

- **FR-01 (Authentication):** Login (mobile + password), token refresh, logout (token blacklist/cookie clear), change password, forgot password workflow, failed-login throttling/lockout, user activation/deactivation.
- **FR-02 (User Management):** CRUD for internal users, role assignment/reassignment, reporting manager hierarchy, password reset by admin, user activity overview.
- **FR-03 (RBAC):** Seed 5 core roles (`Super Admin`, `Admin`, `Management`, `RM`, `MIS Executive`); CRUD for roles; dynamic permission matrix across modules and actions (`view`, `add`, `edit`, `delete`, `import`, `export`, `approve`, `manage`); centralized backend permission evaluator and queryset scoping.
- **FR-04 (Dealer Management):** Add, edit, deactivate, search, filter (dealer code, RM, status), dealer profile view, confirmation history, Excel import with dry-run/row-level validation, Excel export.
- **FR-05 (Campaign Management):** Create, update, activate/close campaigns with campaign code, date range, timezone, and status.
- **FR-06 (Unique Confirmation Links):** Generate cryptographically secure token (`>= 32` bytes entropy), store only SHA-256/HMAC hash, bind to dealer + campaign + RM + `allowed_month` + `expires_at` + `max_submissions`, copy shareable URL & pre-formatted message, mark as shared, deactivate/revoke links, track usage and expiry.
- **FR-07 (Public Confirmation Form):** Validate token status/expiry on load; display exact Havells Sambandh branding and 4 fields (`Dealer Code`, `Mobile Number`, `Preferred Date`, `Preferred Time Slot`); fetch live date/slot availability from backend; validate dealer code + mobile number match; enforce same-month future-only date rule and slot capacity atomically; prevent duplicate submission; display exact approved success message.
- **FR-08 (Scheduling Engine):** Configure operating hours, slot duration (default 60 min), per-slot capacity (default 1), active/inactive slots, holidays, blocked slots; support manual booking, cancellation, and authorized RM/Admin rescheduling with full history.
- **FR-09 (Dashboard & Analytics):** Real-time KPIs (Total Dealers, Total Links, Links Shared, Confirmations Received, Pending Confirmations, Expired Links, Today's Confirmations, Upcoming Bookings) and charts (Daily, Monthly, RM-wise, Campaign-wise, Date-wise, Time-slot utilization, Pending vs Confirmed), filterable by date range and campaign, scoped by RBAC.
- **FR-10 (Reporting & Exports):** 8 standard reports exportable in `.xlsx` and `.csv` with filters (date, campaign, RM, dealer code, status) and strict RBAC enforcement.
- **FR-11 (Notifications & Automation):** Provider-agnostic notification interface (WhatsApp, SMS, Email, In-App) with event hooks for Link Generated, Link Shared, Form Submitted, Link Expired, and Booking Changed; Celery beat task for link expiration sweeps.
- **FR-12 (Audit Logs):** Capture actor, action, module, object type/ID, old/new values (sanitized), IP address, and timestamp; searchable and viewable only by authorized roles.

---

## 7. Non-Functional Requirements

| Category | Requirement | Target / Standard |
| :--- | :--- | :--- |
| **Performance** | API response time (p95) for standard CRUD and public availability checks | ≤ 300 ms under normal load |
| **Performance** | Public form initial page load (LCP on 4G mobile) | ≤ 2.5 seconds |
| **Concurrency** | Simultaneous public booking submissions for the same time slot | Zero overbooking via `SELECT FOR UPDATE` / atomic DB transactions |
| **Availability** | Production uptime target | 99.5%+ with health-check endpoint (`/api/v1/health/`) |
| **Scalability** | Stateless API tier + PostgreSQL + Celery/Redis workers | Horizontally scalable web and worker processes |
| **Responsiveness** | Multi-device UI support | Desktop (1440px+), Laptop (1024px+), Tablet (768px+), Mobile (320px+) |
| **Maintainability** | Layered backend architecture | Views → Serializers → Services / Selectors → Models; no business logic in views |
| **Data Integrity** | Referential integrity & constraints | UUID PKs on business entities, DB unique/check constraints, Django migrations only |
| **Browser Support** | Modern evergreen browsers | Chrome, Safari (iOS/macOS), Edge, Firefox (latest 2 major versions) |
| **Localization / Time** | Authoritative date/time handling | All DB timestamps in UTC; business date rules evaluated in campaign timezone (`Asia/Kolkata`) |

---

## 8. User Journeys

### Journey 1: End-to-End Dealer Confirmation (Primary Happy Path)
1. **Admin / RM** logs in with Mobile Number + Password.
2. **Admin / RM** ensures Dealer exists (added manually or via Excel import) and is assigned to an RM.
3. **Admin / RM** selects the Dealer and active Campaign, then clicks **Generate Confirmation Link**.
4. System generates a cryptographically secure token, stores its hash + `allowed_month` + expiry, and displays the one-time shareable URL (`https://<domain>/confirm/<token>`) and ready-to-share message.
5. **RM** copies the link, shares it via WhatsApp/SMS/Email, and marks the link as **Shared**.
6. **Dealer** taps the link on their mobile phone (no login required).
7. System validates the token and renders the **Date Confirmation Form** showing available future dates within `allowed_month`.
8. **Dealer** enters their **Dealer Code**, **10-digit Mobile Number**, selects an eligible **Preferred Date**, and chooses an available **1-hour Preferred Time Slot**.
9. **Dealer** clicks **Confirm My Date & Time** (button shows loading state and prevents double-click).
10. Backend validates dealer match, mobile match, link status, same-month future date, and slot capacity inside an atomic DB transaction, records the confirmation, marks the link as used, logs the audit event, and returns success.
11. Screen displays the exact approved confirmation message.
12. **Admin / RM Dashboard** immediately reflects the updated confirmation count and slot utilization.

### Journey 2: Dealer Requests Date/Time Change
1. Dealer contacts their RM (as instructed on the success screen).
2. Authorized RM or Admin opens the Confirmation record in the portal.
3. RM/Admin initiates **Reschedule** (or **Cancel**), selecting a new valid date/time slot.
4. Backend atomically releases the old slot capacity, locks and reserves the new slot, preserves booking history, records an audit log entry, and triggers the `Booking Changed` notification hook.

### Journey 3: Bulk Dealer Onboarding by MIS Executive
1. MIS Executive navigates to **Dealer Management → Import Excel**.
2. Downloads the standard Excel template and uploads the populated `.xlsx` file.
3. System validates file type, file size, required columns, mobile number format, unique dealer codes, and assigned RM references.
4. System rejects duplicate/invalid rows without overwriting existing records and displays a row-level error report + import summary.
5. Valid rows are committed cleanly and logged in the Audit Log.

### Journey 4: Dynamic Permission Configuration by Super Admin
1. Super Admin navigates to **Role & Permission Management**.
2. Selects a role (e.g., `Management` or a custom role) and toggles module-level permissions (`view`, `export`, etc.).
3. Changes take effect immediately on the backend permission checks and on the user's next API/session permission sync; Audit Log records old and new permission sets.

---

## 9. Business Rules

All detailed, numbered business rules are documented in [BUSINESS_RULES.md](file:///Users/samaniyastory/Desktop/Projects/HAVELLS_SAMBANDH_Automation_Platform/docs/BUSINESS_RULES.md). Key highlights:
- **BR-AUTH:** 10-digit Indian mobile number (`^[6-9]\d{9}$`) as login identifier; lockout after consecutive failed attempts.
- **BR-RBAC:** Backend-only source of truth; RM queryset isolation by default.
- **BR-LINK:** Cryptographic token (`secrets.token_urlsafe(32)`), SHA-256 hash stored in DB; `allowed_month` locked at generation time (`YYYY-MM`).
- **BR-DATE:** Only strictly future dates (`selected_date > today_in_campaign_tz`) within `allowed_month` are valid; holidays and fully-booked dates are excluded.
- **BR-SLOT:** Configurable operating hours, 60-minute default duration, configurable capacity (default 1), atomic row-level locking on submission.
- **BR-FORM:** Exactly 4 public fields; exact approved success message; no dealer self-edit.

---

## 10. System Constraints

1. **PostgreSQL Primary Database:** PostgreSQL must be used for both primary development and production to guarantee consistent locking (`SELECT FOR UPDATE`), constraints, and JSONB behavior.
2. **Modular Monolith First:** Backend and frontend are cleanly separated repositories/folders (`backend/` and `frontend/`), with the backend structured as a modular monolith of independent Django apps.
3. **No Plain-Text Secrets or Tokens:** Passwords must use Django's password hashers; confirmation tokens must be stored only as cryptographic hashes; secrets live exclusively in environment variables.
4. **No Hardcoded Permissions or Operating Hours:** Roles/permissions and scheduling hours/capacities must be database-driven and admin-configurable.
5. **No Premature External Gateway Coupling:** WhatsApp, SMS, and Email integrations must sit behind clean provider interfaces; v1.0 must function completely without live WhatsApp/SMS credentials.

---

## 11. Security Requirements

1. **Authentication Security:** PBKDF2/Argon2 password hashing, short-lived JWT access tokens (e.g., 15 min) + rotating refresh tokens (e.g., 7 days) stored in `HttpOnly`, `Secure`, `SameSite` cookies (with documented fallback for API clients), token blacklisting on logout, and rate-limited login with account lockout.
2. **Authorization Security:** Every protected endpoint enforces DRF permission classes + centralized `PermissionService` + queryset-level data scoping (RM isolation).
3. **Public Endpoint Hardening:** Rate limiting (DRF throttling) on `/api/v1/public/confirm/*` to prevent token brute-forcing and dealer code/mobile enumeration; uniform error handling that does not leak internal IDs or stack traces.
4. **Input & File Security:** Strict DRF serializer + Zod frontend validation; Excel upload restricted by MIME type, extension (`.xlsx`), and file size limit (e.g., 5 MB); formula-injection sanitization on CSV/Excel exports.
5. **Transport & Web Security:** HTTPS enforced in production, strict CORS allowlist, CSRF protection for cookie-authenticated requests, security headers (HSTS, X-Content-Type-Options, X-Frame-Options, CSP).
6. **Audit & Secret Hygiene:** Sensitive fields (`password`, `token`, `authorization`) scrubbed from all logs and audit trails; `.env` excluded from Git.

---

## 12. Reporting Requirements

All 8 reports must support filtering by **Date Range**, **Campaign**, **RM**, **Dealer Code**, and **Status**, respect the logged-in user's RBAC scope, and export to **Excel (`.xlsx`)** and **CSV (`.csv`)**:

| # | Report Name | Primary Purpose |
| :--- | :--- | :--- |
| 1 | **Dealer Master Report** | Complete directory of authorized dealers, status, assigned RM, and latest confirmation status |
| 2 | **Confirmation Report** | All submitted confirmations with dealer code, RM, campaign, preferred date, time slot, status, and timestamp |
| 3 | **Pending Dealer Report** | Dealers with active/shared links who have not yet submitted a confirmation |
| 4 | **RM-wise Report** | Aggregated performance per RM: assigned dealers, links generated/shared, confirmed, pending, expired, conversion % |
| 5 | **Campaign-wise Report** | Campaign-level summary of reach, confirmations, pending counts, and completion rate |
| 6 | **Date-wise Report** | Daily distribution of confirmed bookings across dates |
| 7 | **Time-slot Report** | Utilization, capacity, and booking counts per 1-hour time slot |
| 8 | **Link Usage Report** | Lifecycle audit of confirmation links (generated, shared, used, expired, deactivated) |

---

## 13. Future Scope (Architectural Readiness Only — Post v1.0)

The v1.0 architecture will include clean extension points (without building full UI/workflows yet) for:
1. Multiple concurrent Dealer Engagement Campaigns
2. Multiple Experience Categories
3. Experience Catalog
4. Experience Budget Management
5. Dealer Reward Management
6. WhatsApp Business API Automation
7. SMS Gateway Automation
8. Automated Reminder Workflows
9. Advanced RM Performance Tracking & Leaderboards
10. Advanced Analytics & Forecasting
11. Multiple Business Units (BU-level partitioning)
12. Organization-Level Hierarchical Permissions
13. Multi-Step Approval Workflows
14. AI-Based Reporting & Natural Language Insights
15. Automated Scheduled MIS Report Delivery

---

## 14. Success Metrics (KPIs)

| Metric | Target | Measurement Method |
| :--- | :--- | :--- |
| **Confirmation Completion Rate** | ≥ 80% of opened valid links result in successful submission | Link Usage vs. Confirmation records |
| **Scheduling Integrity** | 0 overbooked slots; 0 out-of-month bookings | Automated concurrency tests + DB constraints |
| **Authorization Integrity** | 0 cross-RM data leaks; 0 unauthorized mutations | Automated RBAC security test suite |
| **Public Form Time-to-Complete** | < 45 seconds median on mobile | Usability / E2E benchmark |
| **Automated Test Coverage** | ≥ 85% coverage on backend services, permissions, and booking engine | Pytest coverage report |
| **Export Accuracy** | 100% parity between dashboard KPIs and exported Excel/CSV totals | Automated reporting tests |

---

## 15. Acceptance Criteria (v1.0 Definition of Done)

- [ ] **AC-01:** Internal users can log in with Mobile Number + Password, refresh tokens, change passwords, and log out securely; failed logins are rate-limited.
- [ ] **AC-02:** Super Admin can create/edit users, manage roles, and dynamically toggle module/action permissions; backend enforces every permission immediately.
- [ ] **AC-03:** Admin/MIS can add, edit, deactivate, search, filter, import (with row-level validation, no silent overwrites), and export dealers.
- [ ] **AC-04:** RMs can view and generate links only for their assigned dealers; attempts to access other RMs' dealers return `403`/`404`.
- [ ] **AC-05:** Authorized users can generate unique, hashed confirmation links bound to a dealer, campaign, `allowed_month`, and expiry, copy them, mark them shared, and deactivate them.
- [ ] **AC-06:** Dealers can open the public link without login and see only the 4 required fields (`Dealer Code`, `Mobile Number`, `Preferred Date`, `Preferred Time Slot`) with approved Havells Sambandh branding.
- [ ] **AC-07:** Public form rejects mismatched dealer code or mobile number, past dates, current date (unless explicitly configured), dates outside `allowed_month`, holidays, expired/deactivated links, and duplicate submissions.
- [ ] **AC-08:** Concurrent submissions for the final slot capacity allow exactly one booking to succeed and gracefully reject others with a slot-unavailable message.
- [ ] **AC-09:** Successful submission displays the exact approved message: *"Thank You, Your Confirmation form are submited successfully. If you want to change date and time so please connect to your RM."*
- [ ] **AC-10:** Authorized RM/Admin can view schedules, manage operating hours/slots/holidays, and reschedule or cancel bookings with full audit history.
- [ ] **AC-11:** Admin Dashboard displays live DB-backed KPIs and charts with date/campaign filters and RBAC scoping.
- [ ] **AC-12:** All 8 reports export cleanly in Excel (`.xlsx`) and CSV (`.csv`) respecting user permissions.
- [ ] **AC-13:** Audit logs record all critical system events without storing passwords or plain-text tokens.
- [ ] **AC-14:** Backend unit/integration tests, frontend component tests, and the full end-to-end workflow test pass.
- [ ] **AC-15:** Production deployment configuration (Render + PostgreSQL + Redis + Celery) and documentation are complete and verified.

---

## 16. Documented Assumptions & Configurable Decisions

| ID | Topic | Assumption (v1.0 Default) | Configurability |
| :--- | :--- | :--- | :--- |
| **A-01** | Same-day bookings | Same-day bookings are **disallowed** by default (matching the spec example where a link created on 23 Nov allows 24 Nov onward). | Configurable boolean `ALLOW_SAME_DAY_BOOKING` (default `False`). |
| **A-02** | Link generated on last day of month | If no future dates remain in `allowed_month` (e.g., opened on Nov 30), the public form displays a clear "No available dates remain in this month — please contact your RM" message. | Automatic based on `allowed_month` + `Asia/Kolkata` date. |
| **A-03** | Default link expiry | Links default to expiring at `23:59:59` on the last day of `allowed_month` (in `Asia/Kolkata`) unless an earlier custom expiry is set by the Admin/RM. | Configurable per link/campaign. |
| **A-04** | Slot capacity | Default capacity is **1 dealer per 1-hour slot** (global across the campaign/day unless configured otherwise). | Admin-configurable per `TimeSlot` (`max_capacity`). |
| **A-05** | Multiple active links per dealer | Generating a new confirmation link for the same dealer + campaign can optionally deactivate prior unused links to avoid confusion. | Configurable (`AUTO_REVOKE_PRIOR_LINK`, default `True`). |
| **A-06** | Mobile number format | Standard 10-digit Indian mobile numbers (`^[6-9]\d{9}$`), stored normalized as 10 digits (stripping optional `+91`/leading `0` on input). | Validator centralized in `common/validators/`. |
| **A-07** | Forgot password delivery | Since SMS/Email gateways are not pre-configured in v1.0, forgot-password generates a secure reset token via the Notification provider interface (console/log backend in dev; Admin reset always available). | Swappable provider interface in `apps/notifications/`. |
| **A-08** | Exact success message spelling | The exact string specified by stakeholders (*"Thank You, Your Confirmation form are submited successfully. If you want to change date and time so please connect to your RM."*) will be preserved verbatim. | Stored as a single UI constant/config so copy changes are trivial if ever revised. |
