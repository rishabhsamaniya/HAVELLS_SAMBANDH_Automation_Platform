# Screen Specifications — Havells Sambandh

| Field | Value |
| :--- | :--- |
| **Document Version** | 1.0.0 |
| **Phase** | Phase 02 — UI/UX Design Rulebook |
| **Screens Covered** | All 12 Core Application Screens (Internal Portal + Public Dealer Flow) |

---

## Screen 01 — Login Page (`/login`)

- **Audience:** All internal users (Super Admin, Admin, Management, RM, MIS Executive).
- **Layout:** Split desktop layout (`1024px+`) or centered card (`< 1024px`) on `#F8F8F8` background.
  - **Left Brand Panel (Desktop, 45% width):** Clean white/soft-red accented corporate panel displaying `HAVELLS Sambandh`, tagline *"Enterprise Dealer Engagement & Automation Platform"*, and 3 subtle feature highlights (Secure Role-Based Governance, Real-Time Slot Scheduling, Actionable Channel Analytics).
  - **Right Auth Card (55% width, centered white card `max-w-[420px]`):**
    - Brand lockup (visible on mobile/tablet)
    - Heading: **Sign in to your account**
    - Subtitle: *Enter your registered mobile number and password*
    - **Field 1:** `Mobile Number` (`+91` prefix, 10-digit numeric input, `autoComplete="tel"`)
    - **Field 2:** `Password` (with show/hide toggle, `autoComplete="current-password"`)
    - Link: `Forgot password?` (opens Forgot Password modal/view)
    - Primary CTA: **Sign In** (full-width `#D71920`, loading spinner on submit)
- **Error States:** Invalid credentials banner, account deactivated banner, rate-limit/lockout countdown message.

---

## Screen 02 — Admin Dashboard (`/dashboard`)

- **Audience:** All authenticated internal users (data automatically scoped by RBAC — RMs see only their assigned dealers).
- **Header:** Page title `"Dashboard"` + Global Filter Bar (`Campaign` dropdown, `Date Range` selector, `Refresh` button).
- **Section 1 — KPI Grid (8 Cards: 4×2 on Desktop, 2×4 on Tablet, 1×8 on Mobile):**
  1. Total Dealers
  2. Total Confirmation Links
  3. Links Shared
  4. Confirmations Received (with conversion % caption)
  5. Pending Confirmations
  6. Expired Links
  7. Today's Confirmations
  8. Upcoming Bookings
- **Section 2 — Analytics Charts (2-Column Responsive Grid):**
  - **Daily Confirmation Trend** (Bar/Line chart in Havells Red `#D71920`)
  - **Pending vs. Confirmed Comparison** (Donut/Stacked bar in `#16A34A` & `#F59E0B`)
  - **Monthly Confirmation Trend** (Bar chart)
  - **Time-Slot Utilization** (Horizontal bar chart showing bookings vs. capacity per 1-hr slot)
  - **Date-Wise Booking Distribution** (Bar chart across active month dates)
  - **RM-Wise Performance Table/Chart** (Hidden or single-row for RM role; full comparison for Admin/Management/Super Admin)
  - **Campaign-Wise Performance Summary** (Compact table with conversion bars)
- **Loading & Empty States:** Matching skeleton cards/charts while loading; friendly empty state when a campaign has zero activity.

---

## Screen 03 — User Management (`/users`)

- **Audience:** Super Admin, Admin (with `users.view` / `users.manage`).
- **Header:** `"User Management"` + Primary CTA `+ Add User`.
- **Filter Bar:** Search (Name / Mobile Number), Role filter, Status filter (`Active` / `Inactive`), Reporting Manager filter.
- **Data Table Columns:** Full Name, Mobile Number, Email, Assigned Role(s) (badges), Reporting Manager, Status (`Active`/`Inactive`), Last Login, Actions (`Edit`, `Reset Password`, `Deactivate/Activate`, `View Activity`).
- **Modals / Drawers:**
  - **Create / Edit User Modal:** Full Name, Mobile Number (10-digit unique), Email (optional), Password (on create), Role multi/single select, Reporting Manager dropdown, Active toggle.
  - **Reset Password Modal:** New Password + Confirm Password with strength indicator.
  - **User Activity Drawer:** Last login metadata + recent `AuditLog` entries for that user.

---

## Screen 04 — Role Management (`/roles`)

- **Audience:** Super Admin (and users with `roles.view` / `roles.manage`).
- **Header:** `"Role Management"` + Primary CTA `+ Create Role`.
- **Layout:** Clean card grid or data table listing all roles (seeded: `Super Admin`, `Admin`, `Management`, `RM`, `MIS Executive`, plus any custom roles).
- **Columns / Card Data:** Role Name, Code (`super_admin`, `rm`, etc.), Description, Assigned Users Count, Permission Count, Status (`Active`/`Inactive`), Actions (`Edit Role`, `Configure Permissions`, `Toggle Status`).
- **Create / Edit Role Modal:** Role Name, Code (slug, immutable for seeded system roles), Description, Active toggle.

---

## Screen 05 — Permission Management (`/roles/:id/permissions` & `/permissions`)

- **Audience:** Super Admin (and users with `permissions.manage`).
- **Header:** `"Permission Management"` + Role Selector dropdown + `Save Changes` primary CTA (enabled only when dirty).
- **Matrix Layout:**
  - Grouped by Module (`Users`, `Roles & Permissions`, `Dealers`, `Campaigns`, `Confirmation Links`, `Confirmations`, `Scheduling`, `Dashboard`, `Reports`, `Audit Logs`, `Settings`).
  - Columns for standard actions: `View`, `Add`, `Edit`, `Delete`, `Import`, `Export`, `Approve`, `Manage`.
  - Row-level "Select All" toggle + Module-level quick toggle.
  - Unavailable actions for a module display a muted dash (`—`) rather than a misleading checkbox.
- **Feedback:** Sticky bottom bar when unsaved changes exist (`"X permission changes pending"` + `Discard` / `Save Permissions`); displays confirmation toast on save and records audit log.

---

## Screen 06 — Dealer Management (`/dealers`)

- **Audience:** Super Admin, Admin, MIS Executive, Management (read-only), RM (scoped to assigned dealers only).
- **Header:** `"Dealer Management"` + Actions: `Export Excel` (secondary), `Import Excel` (outline-red), `+ Add Dealer` (primary red) — each gated by backend permissions.
- **Filter Bar:** Search by Dealer Code or Mobile Number, Assigned RM filter (hidden/locked to self for RM role), Status filter (`Active` / `Inactive`).
- **Data Table Columns:** Dealer Code (bold `tabular-nums`), Mobile Number, Assigned RM, Status badge, Latest Confirmation Status, Latest Confirmed Date/Slot, Actions (`View Profile`, `Generate Link`, `Edit`, `Deactivate`).
- **Modals / Drawers:**
  - **Add / Edit Dealer Modal:** Dealer Code (uppercase unique), Mobile Number (10-digit), Assigned RM dropdown, Status toggle. *(Note: No Dealer Name required in confirmation form; internal dealer record stays clean and aligned with schema.)*
  - **Import Dealer Excel Modal:** Download Template button → `FileDropzone` (`.xlsx`, max 5 MB) → Upload & Validate → Results Summary card (`Total Rows`, `Created`, `Failed`) + scrollable Row-Level Error Table (`Row #`, `Dealer Code`, `Error Reason`). Never silently overwrites duplicates.
  - **Dealer Profile Drawer:** Dealer summary header, Assigned RM info, quick `Generate Confirmation Link` CTA, Tabs for **Confirmation History** and **Generated Links**.

---

## Screen 07 — Confirmation Link Management (`/confirmation-links`)

- **Audience:** Super Admin, Admin, RM (assigned dealers only), MIS / Management (view only).
- **Header:** `"Confirmation Links"` + Primary CTA `+ Generate Link`.
- **Filter Bar:** Search by Dealer Code, Campaign filter, RM filter (scoped), Status filter (`Active`, `Shared`, `Used`, `Expired`, `Deactivated`), Allowed Month filter (`YYYY-MM`).
- **Data Table Columns:** Dealer Code, Campaign, Assigned RM, Allowed Month (`Nov 2026`), Status badge, Shared At, Expires At, Submissions (`0/1` or `1/1`), Actions (`Mark Shared`, `Deactivate`, `View Details`).
- **Generate Confirmation Link Modal:**
  1. Select Dealer (searchable dropdown, active dealers within user's RM scope).
  2. Select Campaign (active campaigns).
  3. Optional Custom Expiry Date/Time (defaults to end of current month in `Asia/Kolkata`, cannot exceed end of month).
  4. Click **Generate Link**.
  5. **Post-Generation Result View (shown once because raw token is not stored in DB):**
     - `CopyLinkBox` with the full shareable URL (`https://<domain>/confirm/<secure-token>`).
     - Pre-formatted WhatsApp/SMS share message preview with one-click **Copy Message** button.
     - One-click **Mark as Shared** toggle.
     - Security notice: *"For security, this link is hashed and cannot be retrieved again once closed. Copy it now."*

---

## Screen 08 — Public Dealer Confirmation Form (`/confirm/:token`)

- **Audience:** External Havells Dealer (NO login required).
- **Shell:** `PublicLayout` — centered white card (`max-w-[480px]`, `rounded-2xl`, `shadow-modal`) on `#F8F8F8` with top `4px` `#D71920` accent bar.
- **Exact Header & Copy (Mandatory):**
  - Brand Lockup: **HAVELLS** (`#D71920` Bold) **Sambandh** (`#222222` SemiBold)
  - Subtitle pill/caption: **Dealer Engagement Program**
  - Form Title: **Date Confirmation Form**
  - Description: *"Please fill in your details and confirm your preferred date and time."*
- **Form Fields (STRICTLY 4 FIELDS ONLY — No Dealer Name, No Experience, No Email, No Address):**
  1. **Dealer Code** `*` — Text input, placeholder `"Enter your Dealer Code"`, uppercase trim on blur.
  2. **Mobile Number** `*` — 10-digit Indian mobile input (`inputMode="numeric"`, `maxLength={10}`), placeholder `"Enter 10-digit Mobile Number"`.
  3. **Preferred Date** `*` — Custom same-month restricted calendar/date picker showing ONLY strictly future eligible dates within the link's `allowed_month` (server-authoritative `Asia/Kolkata`). Displays subtle helper text: *"Available dates for [Month Year] only"*.
  4. **Preferred Time Slot** `*` — Dropdown populated dynamically after Preferred Date is chosen; displays only available 1-hour slots in readable AM/PM format (e.g., `10:00 AM – 11:00 AM` through `05:00 PM – 06:00 PM`). Shows inline loading state while fetching slots for the chosen date.
- **Primary Submit Button:**
  - Full-width `lg` Havells Red button (`#D71920`, hover `#B5121B`):
  - Exact Label: **`Confirm My Date & Time`**
  - Loading Label (prevents double-click): `Submitting Confirmation...` with spinner.
- **Branded Error & Edge States:**
  - **Invalid Dealer Code / Mobile Mismatch:** Inline field error + top AlertBanner with clear guidance.
  - **Date Outside Allowed Month / Past Date / Holiday:** Prevented in picker AND gracefully handled if returned by backend.
  - **Time Slot Unavailable (race condition):** Top AlertBanner (*"The selected time slot was just booked. Please choose another available slot."*) + automatic refresh of available slots.
  - **No Future Dates Remaining in Month:** Dedicated branded info state inside card (*"No available dates remain in this month. Please contact your RM for assistance."*) with form disabled.
  - **Expired Link / Invalid Token / Deactivated Link:** Full branded status card with `Clock` or `AlertTriangle` icon, clear explanation, and instruction to contact their RM.
  - **Already Submitted Link:** Branded status card showing that confirmation was already recorded, advising the dealer to connect with their RM for any date/time changes.
  - **Server / Network Error:** Clean retryable error banner without technical stack traces.

---

## Screen 09 — Success Confirmation Screen (`/confirm/:token` — Post-Submit State)

- **Audience:** External Havells Dealer immediately after valid form submission.
- **Shell:** Same centered `PublicLayout` card (`max-w-[480px]`).
- **Visual Design:**
  - Top: `HAVELLS Sambandh` compact brand header.
  - Center Hero: Circular `#F0FDF4` badge (`64px`) with `#16A34A` `CheckCircle2` icon (`36px`).
  - Heading: **Confirmation Received**
  - **Exact Approved Message (Verbatim):**
    > *"Thank You, Your Confirmation form are submited successfully. If you want to change date and time so please connect to your RM."*
  - **Confirmed Summary Card (`#F8F8F8`, `1px solid #E5E7EB`, `rounded-xl`):**
    - Dealer Code
    - Confirmed Date (e.g., `Tuesday, 24 November 2026`)
    - Confirmed Time Slot (e.g., `10:00 AM – 11:00 AM`)
  - **No Edit/Resubmit Button:** Dealer cannot self-modify. Browser back/reload hits the backend and renders the "Already Confirmed" state cleanly.

---

## Screen 10 — Schedule Management (`/scheduling`)

- **Audience:** Super Admin, Admin (full management), RM & Management (availability calendar & scoped bookings).
- **Header:** `"Schedule Management"` + Tabs:
  1. **Availability Calendar** — Month grid showing each date's booking count (`Booked / Total Capacity`), holiday badges, and click-to-inspect slot breakdown drawer.
  2. **Operating Hours & Time Slots** — Configure global opening time, closing time, slot duration (default `60 min`), default capacity (default `1`), plus table of individual 1-hour slots with `Active/Inactive` switch and editable `Max Capacity`.
  3. **Holidays & Blocked Slots** — Add/remove full-day holidays and block/unblock specific `(Date, TimeSlot)` pairs with optional reason.
  4. **Bookings & Rescheduling** — Table of all active/cancelled/rescheduled confirmations with filters + actions: `+ Manual Booking`, `Reschedule` (modal with live slot availability & reason), and `Cancel Booking` (with confirmation dialog & reason).

---

## Screen 11 — Reports & Analytics (`/reports`)

- **Audience:** Super Admin, Admin, Management, MIS Executive, RM (scoped to assigned dealers).
- **Header:** `"Reports & Exports"`.
- **Report Selector (Left Tab Rail on Desktop / Horizontal Pill Tabs on Mobile):**
  1. Dealer Master Report
  2. Confirmation Report
  3. Pending Dealer Report
  4. RM-wise Report
  5. Campaign-wise Report
  6. Date-wise Report
  7. Time-slot Report
  8. Link Usage Report
- **Unified Filter Bar:** Date Range, Campaign, RM (locked/hidden for RM role), Dealer Code search, Status filter.
- **Export Actions (Right-Aligned, Permission-Gated):**
  - `Export CSV` (secondary button with `FileText` icon)
  - `Export Excel (.xlsx)` (primary red button with `FileSpreadsheet` icon + loading state)
- **Live Preview Table:** Paginated preview of the exact filtered dataset that will be exported, plus summary totals bar at the top.

---

## Screen 12 — Profile & Settings (`/settings`)

- **Audience:** All authenticated internal users (with Admin-only System Settings tab).
- **Tabs:**
  1. **My Profile:** Read-only Mobile Number & Assigned Role(s), editable Full Name & Email, Last Login timestamp.
  2. **Security & Password:** Change Password form (Current Password, New Password, Confirm New Password) with inline strength rules.
  3. **System Settings (Super Admin / Admin only):** Campaign default timezone (`Asia/Kolkata`), `Allow Same-Day Booking` toggle (default Off), `Auto-Revoke Prior Unused Link` toggle (default On), default slot capacity, and link expiry policy.
  4. **Audit Logs (Super Admin / Admin with `audit_logs.view`):** Filterable table of system audit events (Actor, Action, Module, Object, IP Address, Timestamp) with click-to-open Drawer showing sanitized Before/After diff.
