# REST API Documentation — Havells Sambandh

| Field | Value |
| :--- | :--- |
| **API Version** | `v1` (`/api/v1/`) |
| **Specification** | OpenAPI 3.0 (`drf-spectacular`) |
| **Interactive Docs** | Swagger UI: `/api/v1/docs/` · ReDoc: `/api/v1/redoc/` · Schema JSON/YAML: `/api/v1/schema/` |
| **Authentication** | JWT Bearer Access Token + `HttpOnly` Refresh Cookie (`hs_refresh_token`) |
| **Content-Type** | `application/json` (except Excel upload `multipart/form-data` & `.xlsx`/`.csv` binary exports) |

---

## 1. Standard Response Envelopes

### Success Envelope
```json
{
  "success": true,
  "message": "OK",
  "data": {},
  "meta": {
    "pagination": {
      "count": 42,
      "page": 1,
      "page_size": 20,
      "total_pages": 3
    }
  }
}
```

### Error Envelope (Production-Safe — Never Exposes Stack Traces)
```json
{
  "success": false,
  "error": {
    "code": "TIME_SLOT_UNAVAILABLE",
    "message": "The selected time slot is no longer available. Please choose another slot.",
    "details": {}
  }
}
```

### Standard Query Parameters
- **Pagination:** `?page=1&page_size=20` (max `100`)
- **Search:** `?search=<term>`
- **Ordering:** `?ordering=created_at` or `?ordering=-created_at`

---

## 2. Endpoint Reference

### 2.1 System & Health
| Method | Endpoint | Auth | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health/` | Public | Service health check (`200 OK`) |
| `GET` | `/api/v1/schema/` | Public | OpenAPI 3.0 schema |
| `GET` | `/api/v1/docs/` | Public | Interactive Swagger UI |
| `GET` | `/api/v1/redoc/` | Public | ReDoc API documentation |

### 2.2 Authentication (`/api/v1/auth/`)
| Method | Endpoint | Auth | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/login/` | Public (Throttled) | Mobile + Password login; returns `access` + `user`, sets `HttpOnly` refresh cookie |
| `POST` | `/api/v1/auth/refresh/` | Cookie / Body | Rotates refresh token and issues new `access` token |
| `POST` | `/api/v1/auth/logout/` | Bearer | Blacklists refresh token and clears cookie |
| `GET` | `/api/v1/auth/me/` | Bearer | Returns authenticated user profile, active roles, and effective permissions |
| `PATCH` | `/api/v1/auth/me/` | Bearer | Updates authenticated user's `full_name` and `email` |
| `POST` | `/api/v1/auth/change-password/` | Bearer | Updates password after verifying `current_password` |
| `POST` | `/api/v1/auth/forgot-password/` | Public (Throttled) | Initiates non-enumerating password reset workflow |
| `POST` | `/api/v1/auth/reset-password/` | Public (Throttled) | Confirms reset using `uid`, `token`, and `new_password` |

### 2.3 User Management (`/api/v1/users/`)
| Method | Endpoint | Permission | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/users/` | `users.view` | Paginated users list (filter: `is_active`, `reporting_manager`, `role`; search: name/mobile/email) |
| `POST` | `/api/v1/users/` | `users.add` / `users.manage` | Create user with role & reporting manager assignment |
| `GET` | `/api/v1/users/{id}/` | `users.view` | Retrieve user details |
| `PATCH` | `/api/v1/users/{id}/` | `users.edit` / `users.manage` | Update user profile, manager, or assigned roles |
| `POST` | `/api/v1/users/{id}/deactivate/` | `users.manage` | Deactivate user (blocks self-deactivation & last superuser) |
| `POST` | `/api/v1/users/{id}/activate/` | `users.manage` | Reactivate user and clear lockout |
| `POST` | `/api/v1/users/{id}/reset-password/` | `users.manage` | Admin password reset |
| `GET` | `/api/v1/users/{id}/activity/` | `users.view` | Recent audit activity for the user |

### 2.4 Roles & Permissions (`/api/v1/roles/`, `/api/v1/permissions/`)
| Method | Endpoint | Permission | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/roles/` | `roles.view` | List roles with user counts, permission counts, and assigned permissions |
| `POST` | `/api/v1/roles/` | `roles.add` / `roles.manage` | Create custom role |
| `GET` | `/api/v1/roles/{id}/` | `roles.view` | Role details |
| `PATCH` | `/api/v1/roles/{id}/` | `roles.edit` / `roles.manage` | Update role (blocks deactivating `super_admin`) |
| `GET` | `/api/v1/roles/{id}/permissions/` | `roles.view` / `permissions.view` | List permissions assigned to a role |
| `POST` | `/api/v1/roles/{id}/permissions/` | `permissions.manage` | Replace role permissions dynamically (audited) |
| `GET` | `/api/v1/permissions/` | `permissions.view` | List complete permission catalog (filter: `module`) |

### 2.5 Dealer Management (`/api/v1/dealers/`)
| Method | Endpoint | Permission | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/dealers/` | `dealers.view` (RM-scoped) | Paginated dealer list (filter: `dealer_code`, `assigned_rm`, `status`) |
| `POST` | `/api/v1/dealers/` | `dealers.add` | Create dealer with unique uppercase `dealer_code` |
| `GET` | `/api/v1/dealers/{id}/` | `dealers.view` (RM-scoped) | Dealer profile |
| `PATCH` | `/api/v1/dealers/{id}/` | `dealers.edit` (RM-scoped) | Update dealer details |
| `POST` | `/api/v1/dealers/{id}/deactivate/` | `dealers.delete` (RM-scoped) | Soft-deactivate dealer |
| `GET` | `/api/v1/dealers/{id}/confirmations/` | `dealers.view` (RM-scoped) | Dealer confirmation history |
| `POST` | `/api/v1/dealers/import/` | `dealers.import` | Bulk `.xlsx` import (row-level errors, zero overwrites) |
| `GET` | `/api/v1/dealers/export/` | `dealers.export` (RM-scoped) | Export dealers (`?format=xlsx` or `?format=csv`) |

### 2.6 Campaigns & Confirmation Links (`/api/v1/campaigns/`, `/api/v1/confirmation-links/`)
| Method | Endpoint | Permission | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/campaigns/` | `campaigns.view` | List campaigns |
| `POST` | `/api/v1/campaigns/` | `campaigns.add` | Create campaign |
| `GET` / `PATCH` | `/api/v1/campaigns/{id}/` | `campaigns.view` / `campaigns.edit` | View or update campaign |
| `GET` | `/api/v1/confirmation-links/` | `confirmation_links.view` (RM-scoped) | List confirmation links |
| `POST` | `/api/v1/confirmation-links/` | `confirmation_links.add` (RM-scoped) | Generate secure hashed link; returns one-time `shareable_url` & `share_message` |
| `GET` | `/api/v1/confirmation-links/{id}/` | `confirmation_links.view` (RM-scoped) | Link metadata |
| `POST` | `/api/v1/confirmation-links/{id}/mark-shared/` | `confirmation_links.edit` (RM-scoped) | Mark link shared & stamp `shared_at` |
| `POST` | `/api/v1/confirmation-links/{id}/deactivate/` | `confirmation_links.delete` (RM-scoped) | Immediately revoke link |

### 2.7 Public Dealer Confirmation (`/api/v1/public/confirm/`) — Zero Login
| Method | Endpoint | Auth | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/public/confirm/{token}/` | Token Only (Throttled) | Validate token & return `allowed_month` + eligible future dates (zero internal IDs) |
| `GET` | `/api/v1/public/confirm/{token}/availability/?date=YYYY-MM-DD` | Token Only (Throttled) | Return available 1-hour AM/PM slots for the validated date |
| `POST` | `/api/v1/public/confirm/{token}/submit/` | Token Only (Throttled) | Submit strictly 4 fields (`dealer_code`, `mobile_number`, `preferred_date`, `preferred_time_slot`); atomic booking |

### 2.8 Scheduling (`/api/v1/scheduling/`)
| Method | Endpoint | Permission | Description |
| :--- | :--- | :--- | :--- |
| `GET` / `POST` | `/api/v1/scheduling/config/` | `scheduling.view` / `scheduling.manage` | View or update operating hours & sync time slots |
| `GET` / `POST` | `/api/v1/scheduling/slots/` | `scheduling.view` / `scheduling.add` | List or create time slots |
| `PATCH` | `/api/v1/scheduling/slots/{id}/` | `scheduling.edit` | Update slot `max_capacity` or `is_active` |
| `GET` / `POST` / `DELETE` | `/api/v1/scheduling/holidays/` | `scheduling.view` / `scheduling.add` / `scheduling.manage` | Manage full-day holidays |
| `GET` / `POST` / `DELETE` | `/api/v1/scheduling/blocked-slots/` | `scheduling.view` / `scheduling.edit` | Block or unblock `(date, time_slot)` |
| `GET` | `/api/v1/scheduling/availability/?date=YYYY-MM-DD` | `scheduling.view` | Internal slot capacity & booking counts |
| `GET` / `POST` | `/api/v1/scheduling/bookings/` | `confirmations.view` / `confirmations.add` | List RBAC-scoped bookings or create manual booking |
| `POST` | `/api/v1/scheduling/bookings/{id}/reschedule/` | `confirmations.edit` (RM-scoped) | Atomically reschedule booking with history |
| `POST` | `/api/v1/scheduling/bookings/{id}/cancel/` | `confirmations.edit` (RM-scoped) | Cancel booking & release slot capacity |
| `GET` | `/api/v1/scheduling/bookings/{id}/history/` | `confirmations.view` (RM-scoped) | View booking change history |

### 2.9 Dashboard, Reports & Audit Logs
| Method | Endpoint | Permission | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/dashboard/overview/` | `dashboard.view` (RM-scoped) | 8 live KPI metrics |
| `GET` | `/api/v1/dashboard/analytics/` | `dashboard.view` (RM-scoped) | 7 analytics datasets |
| `GET` | `/api/v1/reports/{dealer-master\|confirmations\|pending\|rm-performance\|campaign-wise\|date-wise\|time-slot\|link-usage}/` | `reports.view` (RM-scoped) | JSON report preview with multi-filters |
| `GET` | `/api/v1/reports/export/?report=<key>&format=xlsx\|csv` | `reports.export` (RM-scoped) | Formula-safe Excel/CSV export (audited) |
| `GET` | `/api/v1/audit-logs/` | `audit_logs.view` | Immutable audit log list (read-only) |
| `GET` | `/api/v1/audit-logs/{id}/` | `audit_logs.view` | Audit log entry detail (read-only) |
