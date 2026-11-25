# Database Schema & ER Design — Havells Sambandh

| Field | Value |
| :--- | :--- |
| **Document Version** | 1.0.0 |
| **Phase** | Phase 04 — Database Design |
| **Database Engine** | PostgreSQL 16+ (Primary Development & Production) |
| **Primary Key Strategy** | UUID v4 (`UUIDField`) across all business entities |
| **Timestamp Strategy** | UTC `TIMESTAMPTZ` (`created_at`, `updated_at`); business dates evaluated in campaign timezone (`Asia/Kolkata`) |
| **Last Updated** | 2026-11-23 |

---

## 1. Entity-Relationship (ER) Diagram

```mermaid
erDiagram
    USERS ||--o{ USERS : "reporting_manager"
    USERS ||--o{ USER_ROLES : "has"
    ROLES ||--o{ USER_ROLES : "assigned_to"
    ROLES ||--o{ ROLE_PERMISSIONS : "grants"
    PERMISSIONS ||--o{ ROLE_PERMISSIONS : "mapped_to"

    USERS ||--o{ DEALERS : "assigned_rm"
    USERS ||--o{ DEALERS : "created_by"
    USERS ||--o{ CAMPAIGNS : "created_by"

    DEALERS ||--o{ CONFIRMATION_LINKS : "receives"
    CAMPAIGNS ||--o{ CONFIRMATION_LINKS : "belongs_to"
    USERS ||--o{ CONFIRMATION_LINKS : "created_by"
    USERS ||--o{ CONFIRMATION_LINKS : "assigned_rm"

    DEALERS ||--o{ CONFIRMATIONS : "submits"
    CAMPAIGNS ||--o{ CONFIRMATIONS : "scoped_to"
    CONFIRMATION_LINKS |o--o{ CONFIRMATIONS : "originates"
    TIME_SLOTS ||--o{ CONFIRMATIONS : "books"
    CONFIRMATIONS ||--o{ CONFIRMATION_HISTORY : "tracks"

    TIME_SLOTS ||--o{ BLOCKED_SLOTS : "blocked_on"
    USERS ||--o{ AUDIT_LOGS : "performed_by"

    USERS {
        uuid id PK
        varchar full_name
        varchar mobile_number UK
        varchar email
        varchar password
        uuid reporting_manager_id FK
        boolean is_active
        boolean is_staff
        boolean is_superuser
        int failed_login_attempts
        timestamptz locked_until
        timestamptz date_joined
        timestamptz last_login
        timestamptz created_at
        timestamptz updated_at
    }

    ROLES {
        uuid id PK
        varchar name UK
        varchar code UK
        text description
        boolean is_system_role
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }

    PERMISSIONS {
        uuid id PK
        varchar name
        varchar codename UK
        varchar module
        varchar action
        text description
        timestamptz created_at
        timestamptz updated_at
    }

    ROLE_PERMISSIONS {
        uuid id PK
        uuid role_id FK
        uuid permission_id FK
        timestamptz created_at
    }

    USER_ROLES {
        uuid id PK
        uuid user_id FK
        uuid role_id FK
        uuid assigned_by_id FK
        timestamptz assigned_at
    }

    DEALERS {
        uuid id PK
        varchar dealer_code UK
        varchar mobile_number
        varchar status
        uuid assigned_rm_id FK
        uuid created_by_id FK
        timestamptz created_at
        timestamptz updated_at
    }

    CAMPAIGNS {
        uuid id PK
        varchar campaign_name
        varchar campaign_code UK
        text description
        date start_date
        date end_date
        varchar timezone
        varchar status
        uuid created_by_id FK
        timestamptz created_at
        timestamptz updated_at
    }

    TIME_SLOTS {
        uuid id PK
        time start_time
        time end_time
        int slot_duration
        int max_capacity
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }

    OPERATING_HOURS_CONFIG {
        uuid id PK
        time opening_time
        time closing_time
        int slot_duration
        int default_capacity
        boolean allow_same_day_booking
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }

    HOLIDAYS {
        uuid id PK
        date date UK
        varchar name
        text description
        boolean is_active
        uuid created_by_id FK
        timestamptz created_at
        timestamptz updated_at
    }

    BLOCKED_SLOTS {
        uuid id PK
        date date
        uuid time_slot_id FK
        varchar reason
        boolean is_active
        uuid created_by_id FK
        timestamptz created_at
        timestamptz updated_at
    }

    CONFIRMATION_LINKS {
        uuid id PK
        uuid dealer_id FK
        varchar token_hash UK
        uuid campaign_id FK
        uuid created_by_id FK
        uuid assigned_rm_id FK
        timestamptz shared_at
        timestamptz expires_at
        varchar allowed_month
        varchar status
        int max_submissions
        int submission_count
        timestamptz created_at
        timestamptz updated_at
    }

    CONFIRMATIONS {
        uuid id PK
        uuid dealer_id FK
        uuid confirmation_link_id FK
        uuid campaign_id FK
        date preferred_date
        uuid preferred_time_slot_id FK
        varchar submission_status
        timestamptz submitted_at
        uuid created_by_id FK
        timestamptz created_at
        timestamptz updated_at
    }

    CONFIRMATION_HISTORY {
        uuid id PK
        uuid confirmation_id FK
        varchar action
        date previous_date
        uuid previous_time_slot_id FK
        date new_date
        uuid new_time_slot_id FK
        text reason
        uuid changed_by_id FK
        timestamptz created_at
    }

    AUDIT_LOGS {
        uuid id PK
        uuid user_id FK
        varchar action
        varchar module
        varchar object_type
        varchar object_id
        jsonb old_values
        jsonb new_values
        inet ip_address
        timestamptz created_at
    }
```

---

## 2. Table Specifications, Constraints & Indexes

### 2.1 `accounts_user` (Custom Django User Model)
- **Purpose:** Primary internal identity table. `USERNAME_FIELD = "mobile_number"`.
- **Constraints:**
  - `mobile_number`: `UNIQUE`, 10-digit Indian mobile number (`^[6-9]\d{9}$`).
  - `email`: Optional (`NULL` allowed); normalized lowercase if provided.
  - `failed_login_attempts >= 0`.
- **Indexes:** `mobile_number` (unique), `is_active`, `reporting_manager_id`.

### 2.2 `roles_role` & `roles_userrole`
- **`roles_role`:** `name` (`UNIQUE`), `code` (`UNIQUE`, indexed), `is_system_role`, `is_active`.
- **`roles_userrole`:** `UNIQUE(user_id, role_id)` preventing duplicate assignment of the same role to a user. Supports multi-role assignment with clear union-based permission resolution.

### 2.3 `permissions_permission` & `permissions_rolepermission`
- **`permissions_permission`:** `codename` (`UNIQUE`, format `<module>.<action>`, e.g., `dealers.import`), `module` (indexed), `action` (indexed).
- **`permissions_rolepermission`:** `UNIQUE(role_id, permission_id)`.

### 2.4 `dealers_dealer`
- **Purpose:** Internal master directory of Havells dealers. Does NOT store dealer name for the public confirmation form.
- **Constraints:**
  - `dealer_code`: `UNIQUE`, trimmed & uppercase-normalized.
  - `mobile_number`: 10-digit Indian mobile number, indexed for search/validation.
  - `status`: `active` | `inactive`.
- **Indexes:** `dealer_code` (unique), `(assigned_rm_id, status)`, `mobile_number`.

### 2.5 `campaigns_campaign`
- **Purpose:** Engagement campaign container (supports future multi-campaign expansion).
- **Constraints:**
  - `campaign_code`: `UNIQUE`, uppercase-normalized.
  - `CHECK (end_date >= start_date)`.
- **Indexes:** `campaign_code` (unique), `status`, `(start_date, end_date)`.

### 2.6 `scheduling_timeslot`, `scheduling_operatinghoursconfig`, `scheduling_holiday`, `scheduling_blockedslot`
- **`scheduling_timeslot`:**
  - `UNIQUE(start_time, end_time)`
  - `CHECK (end_time > start_time)`
  - `CHECK (slot_duration > 0)`
  - `CHECK (max_capacity >= 1)`
- **`scheduling_holiday`:** `date` (`UNIQUE`), `is_active`.
- **`scheduling_blockedslot`:** `UNIQUE(date, time_slot_id)`, indexed on `(date, is_active)`.

### 2.7 `confirmations_confirmationlink`
- **Purpose:** Personalized, hashed confirmation link mapping a dealer + campaign + `allowed_month`.
- **Security:** Stores ONLY SHA-256 hex digest (`token_hash`, 64 chars, `UNIQUE`). Never stores plain-text tokens.
- **Constraints:**
  - `token_hash`: `UNIQUE`.
  - `CHECK (max_submissions >= 1)`.
  - `CHECK (submission_count >= 0 AND submission_count <= max_submissions)`.
- **Indexes:** `token_hash` (unique), `(dealer_id, campaign_id, status)`, `(assigned_rm_id, status)`, `allowed_month`, `expires_at`.

### 2.8 `confirmations_confirmation` & `confirmations_confirmationhistory`
- **`confirmations_confirmation`:**
  - **Partial Unique Index (`uq_active_confirmation_per_link`):** `UNIQUE(confirmation_link_id) WHERE confirmation_link_id IS NOT NULL AND submission_status = 'confirmed'` — prevents duplicate active confirmations for the same link at the database layer.
  - **Indexes:** `(preferred_date, preferred_time_slot_id, submission_status)` (critical for fast capacity counts & locking), `(dealer_id, submitted_at)`, `(campaign_id, submission_status)`.
- **`confirmations_confirmationhistory`:** Immutable ledger of every reschedule or cancellation with actor, old/new date+slot, and reason.

### 2.9 `audit_logs_auditlog`
- **Purpose:** Immutable compliance log of all critical actions.
- **Indexes:** `(module, action)`, `(object_type, object_id)`, `(user_id, created_at)`, `created_at`.
- **JSONB Columns:** `old_values`, `new_values` (automatically redacted of passwords, tokens, and hashes before insert).

---

## 3. Concurrency & Integrity Guarantees

1. **Zero Overbooking:** Booking creation and rescheduling acquire a PostgreSQL row lock (`TimeSlot.objects.select_for_update().get(pk=slot_id)`) inside `transaction.atomic()`, count active `Confirmation` rows for `(preferred_date, preferred_time_slot)`, and abort with `409 Conflict` if `count >= time_slot.max_capacity`.
2. **Zero Duplicate Link Submissions:** `ConfirmationLink.objects.select_for_update()` serializes concurrent submissions on the same token, backed by the partial unique index `uq_active_confirmation_per_link`.
3. **Referential Protection:** Critical foreign keys (`dealer`, `campaign`, `time_slot`, `assigned_rm`) use `on_delete=models.PROTECT` (or `SET_NULL` for optional actor references) so soft-deactivation is enforced and historical audit/report integrity is never broken by cascading deletes.
