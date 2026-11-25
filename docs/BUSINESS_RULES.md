# Business Rules Specification — Havells Sambandh

| Field | Value |
| :--- | :--- |
| **Document Version** | 1.0.0 |
| **Applies To** | v1.0 — Dealer Date Confirmation System & Core Platform |
| **Enforcement Principle** | Every rule below MUST be enforced authoritatively on the backend (Django Services, Serializers, Permissions, and PostgreSQL constraints). Frontend validation is strictly anUX enhancement. |

---

## 1. Authentication & User Lifecycle Rules

| Rule ID | Rule Name | Specification |
| :--- | :--- | :--- |
| **BR-AUTH-01** | Mobile Number as Primary Identifier | Internal users log in with `mobile_number` + `password`. Mobile numbers are normalized to 10 digits matching Indian mobile format `^[6-9]\d{9}$` and must be unique across all users. |
| **BR-AUTH-02** | Password Security | Passwords must never be stored in plain text. Minimum length 8 characters with complexity validation via Django `AUTH_PASSWORD_VALIDATORS`. |
| **BR-AUTH-03** | Inactive User Blocking | Users with `is_active = False` cannot log in, refresh tokens, or call any protected endpoint. Deactivating a user invalidates active refresh tokens immediately. |
| **BR-AUTH-04** | Failed Login Lockout | Consecutive failed logins (default threshold: **5 attempts within 15 minutes**) trigger temporary lockout/throttling and log a security event. |
| **BR-AUTH-05** | Self-Deactivation Guard | A Super Admin cannot deactivate their own account or remove the last active Super Admin role in the system. |

---

## 2. Role-Based Access Control (RBAC) & Data Isolation Rules

| Rule ID | Rule Name | Specification |
| :--- | :--- | :--- |
| **BR-RBAC-01** | Database-Driven Permissions | Roles, permissions, and role-permission mappings are stored in PostgreSQL. No role-to-permission mappings may be hardcoded in React or scattered across Django views. |
| **BR-RBAC-02** | Super Admin Override | Users holding an active `Super Admin` role (or `is_superuser = True`) have full system access across all modules and scopes. |
| **BR-RBAC-03** | Effective Permission Resolution | When a user holds multiple active roles, effective permissions are the **union** of permissions across all their active roles. Inactive roles contribute zero permissions. |
| **BR-RBAC-04** | RM Data Isolation | A user whose effective scope is RM-level (e.g., `RM` role without org-wide view permission) may ONLY read, generate links for, view confirmations of, and export data for dealers where `dealer.assigned_rm == current_user`. |
| **BR-RBAC-05** | Unauthorized Resource Response | Attempting to access another RM's dealer or confirmation link returns `403 Forbidden` or `404 Not Found` (filtered at queryset level) without leaking record existence. |
| **BR-RBAC-06** | Management Default Read-Only | The seeded `Management` role receives `view` and `export` permissions across dashboards and reports; write permissions (`add`, `edit`, `delete`) are disabled by default but configurable by Super Admin. |

---

## 3. Dealer Management & Excel Import Rules

| Rule ID | Rule Name | Specification |
| :--- | :--- | :--- |
| **BR-DLR-01** | Unique Dealer Code | `dealer_code` is mandatory, trimmed, case-normalized (uppercase), and globally unique in the `dealers` table. |
| **BR-DLR-02** | Dealer Mobile Validation | `mobile_number` is mandatory and must be a valid 10-digit Indian mobile number (`^[6-9]\d{9}$`). |
| **BR-DLR-03** | Internal Management Only | Dealers do not have user accounts and cannot access internal portal routes or authenticated APIs. |
| **BR-DLR-04** | Inactive Dealer Restrictions | New confirmation links cannot be generated for inactive dealers (`status != 'active'`). Existing historical confirmations remain intact for reporting. |
| **BR-DLR-05** | Excel Import File Validation | Only `.xlsx` files up to **5 MB** (configurable) are accepted. Required columns (`dealer_code`, `mobile_number`, `assigned_rm_mobile` or `assigned_rm_id`, optional `status`) must be present before row processing begins. |
| **BR-DLR-06** | No Silent Overwrites on Import | If an imported row contains a `dealer_code` that already exists in the database (or is duplicated within the uploaded file), that row MUST be rejected with a clear row-level error message. Existing records are never silently overwritten. |
| **BR-DLR-07** | Row-Level Import Summary | Every import returns: `total_rows`, `created_count`, `failed_count`, and a list of `{row_number, dealer_code, errors[]}`. |

---

## 4. Unique Confirmation Link Rules

| Rule ID | Rule Name | Specification |
| :--- | :--- | :--- |
| **BR-LNK-01** | Cryptographic Token & Hash Storage | Tokens are generated using `secrets.token_urlsafe(32)` (256-bit entropy). The raw token is returned **once** upon generation to build the shareable URL (`https://<domain>/confirm/<token>`) and is NEVER stored in plain text in the database or logs. Only its SHA-256 hex digest (`token_hash`) is persisted. |
| **BR-LNK-02** | No Internal ID Exposure | Public URLs and public API payloads must never expose internal database UUIDs/IDs of dealers, users, RMs, or links. |
| **BR-LNK-03** | Allowed Month Locking | At link generation time, `allowed_month` (`YYYY-MM`) is computed and locked from the current date in the campaign's timezone (default `Asia/Kolkata`). |
| **BR-LNK-04** | Default & Custom Expiry | If `expires_at` is not explicitly provided, it defaults to `23:59:59` on the final calendar day of `allowed_month` in the campaign timezone. Custom `expires_at` cannot exceed the end of `allowed_month`. |
| **BR-LNK-05** | Submission Limit | `max_submissions` defaults to `1`. Once submissions reach `max_submissions`, the link status transitions to `used` and rejects further submissions. |
| **BR-LNK-06** | Prior Link Handling | By default (`AUTO_REVOKE_PRIOR_LINK = True`), generating a new link for the same `(dealer, campaign)` automatically deactivates any previous unused active link for that pair, preventing conflicting links. |
| **BR-LNK-07** | Link Expiration Enforcement | Both lazy validation (on every public request: `now() > expires_at`) and a periodic Celery task mark expired links as `expired`. |

---

## 5. Same-Month Date Restriction Rules (Critical)

| Rule ID | Rule Name | Specification |
| :--- | :--- | :--- |
| **BR-DATE-01** | Authoritative Server Clock & Timezone | All date eligibility calculations use the backend server clock converted to the campaign's configured timezone (default: `Asia/Kolkata`). Client device clocks are never trusted. |
| **BR-DATE-02** | Strict Same-Month Window | `selected_date` MUST belong to the exact year and month stored in `confirmation_link.allowed_month`. Dates in prior or subsequent months are rejected (`DATE_OUTSIDE_ALLOWED_MONTH`). |
| **BR-DATE-03** | Strictly Future Dates Only | `selected_date` MUST be strictly greater than `today` in the campaign timezone (`selected_date > today`), unless `ALLOW_SAME_DAY_BOOKING` is explicitly enabled (default: `False`). Example: Link created on `2026-11-23` → allowed dates are `2026-11-24` through `2026-11-30` only; `2026-11-22`, `2026-11-23`, and `2026-12-01` are rejected. |
| **BR-DATE-04** | No Remaining Dates Edge Case | If no eligible future dates exist in `allowed_month` (e.g., today is the last day of `allowed_month`, or all remaining dates are holidays/fully booked), the availability endpoint returns `available_dates: []` with reason code `NO_DATES_AVAILABLE_IN_MONTH`, and the UI displays a clear branded unavailable message instructing the dealer to contact their RM. |
| **BR-DATE-05** | Holiday Exclusion | Dates configured as active holidays in the scheduling engine cannot be selected and are rejected on submission (`DATE_IS_HOLIDAY`). |

---

## 6. Time Slot, Scheduling & Concurrency Rules

| Rule ID | Rule Name | Specification |
| :--- | :--- | :--- |
| **BR-SLOT-01** | Configurable One-Hour Slots | Time slots are generated from admin-configured operating hours (default `10:00` to `18:00`, `slot_duration = 60` minutes → 8 slots) and formatted in readable AM/PM style (e.g., `10:00 AM – 11:00 AM`). |
| **BR-SLOT-02** | Active & Unblocked Slots Only | Only slots where `is_active = True` and not blocked for the target date are returned as selectable and accepted on submission. |
| **BR-SLOT-03** | Capacity Enforcement | Active confirmed bookings for `(preferred_date, preferred_time_slot)` MUST NOT exceed `time_slot.max_capacity` (default `1`). Cancelled or rescheduled-away bookings do not count toward active capacity. |
| **BR-SLOT-04** | Atomic Concurrency Control | Public submission and manual booking/rescheduling MUST execute inside `transaction.atomic()` with row-level locking (`select_for_update()`) on the `ConfirmationLink` and `TimeSlot` (or date-slot lock record) before re-checking availability and inserting the `Confirmation`. |
| **BR-SLOT-05** | Duplicate Submission Prevention | A database unique constraint (partial unique index on active confirmation per `confirmation_link`) plus service-level locking guarantees a link cannot produce duplicate active confirmations even under simultaneous double-click or replay attacks. |

---

## 7. Public Confirmation Form Rules

| Rule ID | Rule Name | Specification |
| :--- | :--- | :--- |
| **BR-FORM-01** | Exact Four Fields Only | The public form collects ONLY: (1) `Dealer Code`, (2) `Mobile Number`, (3) `Preferred Date`, (4) `Preferred Time Slot`. Never collect Dealer Name, Experience, Email, Address, or other PII. |
| **BR-FORM-02** | Strict Dealer Verification | Submitted `dealer_code` (case-insensitive trimmed match) AND `mobile_number` (normalized 10-digit match) must both match the `Dealer` record linked to the `ConfirmationLink`. Mismatches return user-friendly validation errors (`INVALID_DEALER_CODE` / `MOBILE_NUMBER_MISMATCH`). |
| **BR-FORM-03** | Exact Success Message | Upon successful submission, the UI MUST display verbatim: *"Thank You, Your Confirmation form are submited successfully. If you want to change date and time so please connect to your RM."* |
| **BR-FORM-04** | No Self-Service Modification | Once confirmed, the dealer cannot modify or cancel their submission via the public link. Re-opening a used link displays an "Already Confirmed" status screen advising the dealer to contact their RM. |
| **BR-FORM-05** | Authorized Rescheduling / Cancellation | Only authorized internal users (Admin, Super Admin, or permitted RM for their assigned dealers) may reschedule or cancel a confirmation. Every change records `old_values`, `new_values`, reason, actor, and timestamp in the Audit Log. |

---

## 8. Reporting & Audit Rules

| Rule ID | Rule Name | Specification |
| :--- | :--- | :--- |
| **BR-RPT-01** | Permission-Scoped Data | Every report query and export applies the exact same queryset-level RBAC filter as the UI (e.g., RMs only export their assigned dealers). |
| **BR-RPT-02** | Spreadsheet Formula Safety | CSV and Excel exports must neutralize leading formula characters (`=`, `+`, `-`, `@`) in user-supplied text fields to prevent CSV/Excel formula injection. |
| **BR-AUD-01** | Mandatory Audit Trail | All state-changing actions across Users, Roles, Permissions, Dealers, Campaigns, Links, Confirmations, Scheduling, and Report Exports must write an `AuditLog` entry. |
| **BR-AUD-02** | Secret Redaction | Audit log `old_values` and `new_values` must automatically strip/redact `password`, `token`, `token_hash`, and `refresh` fields. |
