# Feature List — Havells Sambandh

| Field | Value |
| :--- | :--- |
| **Document Version** | 1.0.0 |
| **Release Scope** | v1.0 (Dealer Date Confirmation System) + Future Roadmap |
| **Priority Key** | `P0` = Must-have for v1.0 Launch · `P1` = High-value v1.0 · `P2` = Post-v1.0 Future Scope |

---

## 1. Authentication & Security (`M01`)

| Feature ID | Feature Name | Description | Priority | Roles |
| :--- | :--- | :--- | :--- | :--- |
| **F-01.01** | Mobile + Password Login | Authenticate internal users using 10-digit Indian mobile number and password | P0 | All Internal |
| **F-01.02** | JWT Token Lifecycle | Access token + rotating refresh token with secure HttpOnly cookie support | P0 | All Internal |
| **F-01.03** | Secure Logout | Blacklist refresh token and clear session cookies | P0 | All Internal |
| **F-01.04** | Change Password | Authenticated user password update with current-password verification | P0 | All Internal |
| **F-01.05** | Forgot Password Workflow | Tokenized reset flow via notification provider interface + Admin password reset | P1 | All Internal |
| **F-01.06** | Failed Login Protection | Rate limiting and temporary lockout after consecutive invalid login attempts | P0 | System |
| **F-01.07** | Account Activation / Deactivation | Immediately revoke access for deactivated users without deleting audit history | P0 | Super Admin, Admin |

---

## 2. User Management (`M01`)

| Feature ID | Feature Name | Description | Priority | Roles |
| :--- | :--- | :--- | :--- | :--- |
| **F-02.01** | Create User | Add internal user with full name, unique mobile number, optional email, role, and reporting manager | P0 | Super Admin, Admin |
| **F-02.02** | Edit User | Update user profile, status, role assignment, and reporting manager | P0 | Super Admin, Admin |
| **F-02.03** | Deactivate / Reactivate User | Toggle `is_active` safely with audit trail | P0 | Super Admin, Admin |
| **F-02.04** | Admin Password Reset | Reset user password securely and force re-authentication | P1 | Super Admin, Admin |
| **F-02.05** | Search & Filter Users | Filter users by role, status, reporting manager, mobile number, or name | P0 | Super Admin, Admin |
| **F-02.06** | View User Activity | Inspect last login and recent audit activity for a user | P1 | Super Admin, Admin |

---

## 3. Dynamic RBAC — Roles & Permissions (`M02`)

| Feature ID | Feature Name | Description | Priority | Roles |
| :--- | :--- | :--- | :--- | :--- |
| **F-03.01** | Seed Core Roles | Seed `Super Admin`, `Admin`, `Management`, `RM`, and `MIS Executive` via idempotent management command | P0 | System |
| **F-03.02** | Role CRUD | Create, edit, activate/deactivate custom and standard roles | P0 | Super Admin |
| **F-03.03** | Permission Catalog | Granular permissions per module across `view`, `add`, `edit`, `delete`, `import`, `export`, `approve`, `manage` | P0 | Super Admin |
| **F-03.04** | Dynamic Role-Permission Matrix | Interactive UI and API to assign/revoke permissions per role | P0 | Super Admin |
| **F-03.05** | Centralized Permission Service | Backend enforcement via DRF permission classes + queryset scoping (RM isolation) | P0 | System |
| **F-03.06** | Dynamic Frontend Navigation | Fetch effective user permissions from API to render authorized menu items and action buttons | P0 | All Internal |

---

## 4. Dealer Management (`M03`)

| Feature ID | Feature Name | Description | Priority | Roles |
| :--- | :--- | :--- | :--- | :--- |
| **F-04.01** | Add Dealer | Register dealer with unique `dealer_code`, 10-digit `mobile_number`, `status`, and `assigned_rm` | P0 | Super Admin, Admin, MIS |
| **F-04.02** | Edit Dealer | Update dealer mobile number, status, or RM assignment | P0 | Super Admin, Admin, MIS |
| **F-04.03** | Deactivate Dealer | Soft-deactivate dealer while preserving historical confirmations and audit logs | P0 | Super Admin, Admin |
| **F-04.04** | Search & Filter Dealers | Search by dealer code/mobile; filter by RM and status (RM sees only assigned dealers) | P0 | All Authorized |
| **F-04.05** | Dealer Profile & History | View dealer metadata, generated links, and complete confirmation history | P0 | All Authorized |
| **F-04.06** | Bulk Excel Import | Upload `.xlsx` with schema validation, duplicate detection, row-level errors, summary report, and zero silent overwrites | P0 | Super Admin, Admin, MIS |
| **F-04.07** | Dealer Excel Export | Export permission-filtered dealer directory to `.xlsx` / `.csv` | P0 | Super Admin, Admin, MIS, Management |

---

## 5. Campaign Management (`M04`)

| Feature ID | Feature Name | Description | Priority | Roles |
| :--- | :--- | :--- | :--- | :--- |
| **F-05.01** | Create & Edit Campaign | Define campaign name, unique code, description, start/end dates, timezone, and status | P0 | Super Admin, Admin |
| **F-05.02** | Campaign List & Filtering | Filter campaigns by status and date range | P0 | All Authorized |
| **F-05.03** | Campaign Activation / Closure | Transition campaign lifecycle states (`draft`, `active`, `paused`, `completed`, `archived`) | P1 | Super Admin, Admin |

---

## 6. Unique Confirmation Link Management (`M06`)

| Feature ID | Feature Name | Description | Priority | Roles |
| :--- | :--- | :--- | :--- | :--- |
| **F-06.01** | Generate Personalized Link | Create cryptographically secure token mapped to dealer + campaign + RM + `allowed_month` + expiry; store hash only | P0 | Super Admin, Admin, RM |
| **F-06.02** | Copy Link & Share Message | One-click copy of shareable URL and formatted WhatsApp/SMS/Email message | P0 | Super Admin, Admin, RM |
| **F-06.03** | Mark Link as Shared | Track `shared_at` timestamp when RM/Admin shares link externally | P0 | Super Admin, Admin, RM |
| **F-06.04** | Deactivate / Revoke Link | Immediately invalidate an unused link with audit logging | P0 | Super Admin, Admin, RM (own) |
| **F-06.05** | Link Usage & Expiry Tracking | Monitor statuses (`active`, `shared`, `used`, `expired`, `deactivated`) and automated expiry sweeps | P0 | All Authorized |

---

## 7. Public Dealer Date Confirmation Form (`M07`)

| Feature ID | Feature Name | Description | Priority | Roles |
| :--- | :--- | :--- | :--- | :--- |
| **F-07.01** | Branded Public Form | Responsive Havells Sambandh form (Red & White, Poppins) requiring no login | P0 | Public Dealer (Token) |
| **F-07.02** | Strict 4-Field Input | Collect only `Dealer Code`, `Mobile Number`, `Preferred Date`, and `Preferred Time Slot` | P0 | Public Dealer (Token) |
| **F-07.03** | Dealer & Mobile Verification | Validate dealer code and 10-digit mobile number against the link's registered dealer | P0 | System |
| **F-07.04** | Same-Month Future Date Picker | Restrict selection to strictly future dates in `allowed_month` (backend-authoritative `Asia/Kolkata`) | P0 | System |
| **F-07.05** | Live 1-Hour Slot Availability | Dynamically load available AM/PM 1-hour time slots for the chosen date; hide/disable full or blocked slots | P0 | System |
| **F-07.06** | Concurrency-Safe Submission | Atomic DB transaction + row-level lock preventing duplicate submission and slot overbooking | P0 | System |
| **F-07.07** | Double-Submit Protection | Loading state and disabled submit button (`Confirm My Date & Time`) during in-flight request | P0 | Public Dealer (Token) |
| **F-07.08** | Approved Success Screen | Display verbatim stakeholder success message with RM contact guidance | P0 | Public Dealer (Token) |
| **F-07.09** | Branded Error & Edge States | Dedicated UX for expired link, invalid token, already submitted, no remaining dates in month, mismatch errors, and slot taken | P0 | Public Dealer (Token) |

---

## 8. Scheduling Management (`M05`)

| Feature ID | Feature Name | Description | Priority | Roles |
| :--- | :--- | :--- | :--- | :--- |
| **F-08.01** | Operating Hours & Slot Config | Configure opening time, closing time, slot duration (default 60 min), and default capacity (default 1) | P0 | Super Admin, Admin |
| **F-08.02** | Time Slot Management | Activate/deactivate slots and adjust per-slot max capacity | P0 | Super Admin, Admin |
| **F-08.03** | Holiday & Blocked Slot Management | Mark holidays (full day) or block/unblock specific date+slot combinations | P0 | Super Admin, Admin |
| **F-08.04** | Availability Calendar View | Inspect date-wise and slot-wise booking counts vs. remaining capacity | P0 | All Authorized |
| **F-08.05** | Manual Booking & Rescheduling | Authorized Admin/RM workflow to manually create, reschedule, or cancel a dealer confirmation with history | P0 | Super Admin, Admin, RM (if permitted) |

---

## 9. Admin Dashboard & Analytics (`M08`)

| Feature ID | Feature Name | Description | Priority | Roles |
| :--- | :--- | :--- | :--- | :--- |
| **F-09.01** | Executive KPI Cards | Total Dealers, Total Links, Links Shared, Confirmations Received, Pending, Expired, Today's Confirmations, Upcoming Bookings | P0 | All Internal (Scoped) |
| **F-09.02** | Interactive Analytics Charts | Daily & monthly confirmation trends, RM-wise performance, Campaign-wise performance, Date-wise distribution, Time-slot utilization, Pending vs Confirmed | P0 | All Internal (Scoped) |
| **F-09.03** | Global Dashboard Filters | Filter all KPIs and charts by date range and campaign | P0 | All Internal (Scoped) |

---

## 10. Reporting & Exports (`M09`)

| Feature ID | Feature Name | Description | Priority | Roles |
| :--- | :--- | :--- | :--- | :--- |
| **F-10.01** | 8 Standard Reports | Dealer Master, Confirmation, Pending Dealer, RM-wise, Campaign-wise, Date-wise, Time-slot, Link Usage | P0 | Authorized Roles (Scoped) |
| **F-10.02** | Multi-Criteria Filtering | Filter by Date Range, Campaign, RM, Dealer Code, and Status | P0 | Authorized Roles |
| **F-10.03** | Excel (`.xlsx`) & CSV Export | Formatted OpenPyXL/Pandas exports enforcing RBAC and CSV formula-injection protection | P0 | Authorized Roles |

---

## 11. Notifications, Automation & Audit (`M10`, `M11`)

| Feature ID | Feature Name | Description | Priority | Roles |
| :--- | :--- | :--- | :--- | :--- |
| **F-11.01** | Notification Provider Interface | Pluggable adapters for WhatsApp, SMS, Email, and In-App notifications | P1 | System |
| **F-11.02** | Lifecycle Automation Hooks | Event emitters for Link Generated, Link Shared, Form Submitted, Link Expired, Booking Changed | P1 | System |
| **F-11.03** | Celery Scheduled Expiry Sweep | Periodic Celery task marking past-expiry links as `expired` | P1 | System |
| **F-11.04** | Comprehensive Audit Logging | Immutable log of actor, action, module, object ref, sanitized old/new values, IP, timestamp | P0 | Super Admin, Admin |

---

## 12. Future Scope Roadmap (`P2` — Post v1.0)

- **F-12.01:** Multi-campaign orchestration & templates
- **F-12.02:** Experience categories & interactive Experience Catalog
- **F-12.03:** Experience budget & dealer reward management
- **F-12.04:** Live WhatsApp Business API & SMS gateway delivery with automated reminders
- **F-12.05:** Multi-Business-Unit (BU) partitioning & hierarchical org permissions
- **F-12.06:** Multi-step approval workflows
- **F-12.07:** AI-assisted reporting & automated scheduled MIS email delivery
