# Component Library Specification — Havells Sambandh

| Field | Value |
| :--- | :--- |
| **Document Version** | 1.0.0 |
| **Phase** | Phase 02 — UI/UX Design Rulebook |
| **Location (Phase 03+)** | `frontend/src/components/ui/` and `frontend/src/components/shared/` |
| **Dependencies** | React, TypeScript, Tailwind CSS, Lucide React |

---

## 1. Component Architecture Principles

1. **Single Source of Truth:** Every button, input, modal, table, badge, and card across all 12 screens MUST be built from this shared component library — never ad-hoc styled `<button>` or `<input>` tags.
2. **Strict TypeScript Props:** Every component exports typed props extending native HTML attributes where applicable.
3. **Accessible by Default:** Proper `id`/`htmlFor` pairing, `aria-invalid`, `aria-describedby`, `role="alert"`, focus trapping in modals, and keyboard `Escape` handling.
4. **Zero Business Logic in UI Primitives:** Components in `components/ui/` are purely presentational; domain logic lives in `features/*` and hooks.

---

## 2. Core UI Primitives (`components/ui/`)

### 2.1 `Button`
| Variant | Background | Text | Border | Hover |
| :--- | :--- | :--- | :--- | :--- |
| `primary` | `#D71920` | `#FFFFFF` | none | `#B5121B` |
| `secondary` | `#FFFFFF` | `#222222` | `1px solid #E5E7EB` | `#F8F8F8` |
| `outline-red` | `#FFFFFF` | `#D71920` | `1px solid #D71920` | `#FEF2F2` |
| `ghost` | `transparent` | `#222222` | none | `#F3F4F6` |
| `danger` | `#DC2626` | `#FFFFFF` | none | `#B91C1C` |

- **Sizes:** `sm` (`34px` height, `px-3 text-xs`), `md` (`40px` height, `px-4 text-sm`), `lg` (`46px` height, `px-6 text-sm` — used for Login & Public Confirmation CTA).
- **Props:** `variant`, `size`, `isLoading`, `loadingText`, `leftIcon`, `rightIcon`, `fullWidth`, `disabled`.
- **States:** Focus ring `focus-visible:ring-2 focus-visible:ring-[#D71920]/40 focus-visible:ring-offset-2`; disabled opacity `50%` with `cursor-not-allowed`; `isLoading` disables clicks and renders inline `Loader2` spinner.

### 2.2 `TextInput`
- **Anatomy:** Label (with optional red `*`), Input container (`42px` height, `rounded-lg`, `border #E5E7EB`, white bg, optional left/right icon or prefix such as `+91`), Helper text or Error text (`#DC2626`).
- **States:**
  - Focus: `border-[#D71920] ring-2 ring-[#D71920]/15`
  - Error: `border-[#DC2626] ring-2 ring-[#DC2626]/15`
  - Disabled / ReadOnly: `bg-[#F3F4F6] text-[#6B7280] cursor-not-allowed`
- **Password Variant (`PasswordInput`):** Built-in show/hide eye toggle button (`aria-label="Toggle password visibility"`).

### 2.3 `SelectInput`
- **Anatomy:** Styled select / custom accessible dropdown matching `TextInput` height (`42px`) and border tokens.
- **Features:** Placeholder option, disabled options (for unavailable time slots if ever shown, though public form hides or disables unavailable slots per spec), loading skeleton/spinner state while fetching slots, inline error support.

### 2.4 `DatePicker` (Same-Month Restricted Calendar)
- **Purpose:** Used on the Public Dealer Confirmation Form and internal Scheduling/Reschedule dialogs.
- **Props:** `value`, `onChange`, `allowedDates: string[]` (authoritative list from backend), `allowedMonth: string` (`YYYY-MM`), `disabledDates`, `isLoading`, `error`.
- **Behavior:**
  - Locks month navigation to `allowedMonth` on the public form (prev/next month arrows hidden or disabled).
  - Past dates, current date (when disallowed), holidays, and fully-booked dates render visually muted (`#D1D5DB`, line-through/disabled) and non-clickable.
  - Eligible dates render selectable in `#222222`; selected date fills with `#D71920` and white text.
  - When `allowedDates.length === 0`, renders an inline unavailable banner instead of an interactive grid.

### 2.5 `StatusBadge`
- Pill-shaped (`rounded-full px-2.5 py-0.5 text-xs font-medium inline-flex items-center gap-1.5`) with optional `6px` status dot.
- **Mapped Semantic Presets:**
  - `confirmed`, `active`, `completed` → Success (`#16A34A` on `#F0FDF4`)
  - `pending`, `shared`, `rescheduled` → Warning (`#B45309` on `#FFFBEB`, dot `#F59E0B`)
  - `expired`, `deactivated`, `cancelled`, `inactive`, `failed` → Error (`#DC2626` on `#FEF2F2`)
  - `used`, `draft`, `archived` → Neutral (`#374151` on `#F3F4F6`)

### 2.6 `Card` & `KPICard`
- **`Card`:** White surface (`#FFFFFF`), `1px solid #E5E7EB`, `rounded-xl`, `shadow-card`, optional `header` (title, subtitle, right action slot) and `footer`.
- **`KPICard`:** Specialized dashboard metric card displaying:
  - Top row: Metric label (`13px` `#6B7280` Medium) + subtle icon container (`36px` rounded-lg `#FEF2F2` with `#D71920` icon or semantic tint).
  - Middle: Large bold `28px` `tabular-nums` value (`#222222`).
  - Bottom: Optional secondary caption (e.g., `"of 240 total links"` or percentage conversion).

### 2.7 `DataTable`
- **Features:**
  - Sticky subtle gray header (`#F8F8F8`), uppercase `12px` SemiBold column titles.
  - Row hover highlight (`#F9FAFB`), crisp `1px solid #E5E7EB` row dividers.
  - Built-in server-side pagination footer (`Showing 1–20 of 145`, page size selector `10/25/50`, Prev/Next buttons).
  - Sortable column headers with subtle chevron indicator.
  - Loading state (`TableSkeleton` with animated shimmer rows).
  - Empty state (`EmptyState` component with icon, title, message, and optional CTA).
  - Mobile responsive wrapper (`overflow-x-auto`) with sticky first/action columns where needed.

### 2.8 `Modal` & `SlideOverDrawer`
- **`Modal`:** Centered overlay (`bg-black/40 backdrop-blur-[1px]`), white `rounded-2xl` container (`sm: 440px`, `md: 560px`, `lg: 720px`), sticky header with title + close `X`, scrollable body, sticky footer with Cancel (secondary) + Primary CTA.
- **`ConfirmDialog`:** Specialized confirmation modal for destructive actions (Deactivate User, Deactivate Dealer, Revoke Link, Cancel Booking) with warning icon and explicit action label.
- **`SlideOverDrawer`:** Right-aligned panel (`480px` wide) for viewing Dealer Profile, Confirmation History, or Audit Log before/after JSON diffs without losing table scroll position.

### 2.9 `AlertBanner` & `Toast`
- **`AlertBanner`:** Inline feedback banner (`success`, `warning`, `error`, `info`) with Lucide icon, bold title, descriptive copy, and optional close button.
- **`Toast`:** Top-right floating notifications (`auto-dismiss 4s` for success/info, `6s` or manual dismiss for errors), stacked cleanly up to 3 visible.

### 2.10 `FileDropzone`
- Dashed border (`#D1D5DB`, turns `#D71920` on drag-over), `.xlsx` file type badge, max-size label (`Max 5 MB`), selected file preview with remove button, and download-template link.

### 2.11 `PermissionGate`
- Structural wrapper `<PermissionGate permission="dealers.add">` that conditionally renders UI controls based on effective backend-provided permissions. **Note:** Strictly a UX convenience; every action is independently enforced on the Django backend.

---

## 3. Shared Brand Components (`components/shared/`)

| Component | Purpose |
| :--- | :--- |
| `BrandLogo` | Renders the `HAVELLS Sambandh` lockup in `sm` (sidebar/header) and `lg` (login & public form) variants. |
| `PageHeader` | Standardized internal page top bar: Title, optional subtitle, breadcrumb trail, and right-aligned action buttons. |
| `FilterBar` | Unified horizontal/wrapping filter toolbar for search input, dropdown filters (Campaign, RM, Status), date range picker, and Reset Filters button. |
| `CopyLinkBox` | Read-only URL display with one-click Copy URL button, Copy WhatsApp/SMS Message button, and visual `"Copied!"` confirmation state. |
| `EmptyState` | Centered minimal illustration/icon, clear heading, helper text, and optional primary action button. |
| `ErrorBoundaryFallback` | Branded recovery screen if an unexpected client runtime error occurs. |
