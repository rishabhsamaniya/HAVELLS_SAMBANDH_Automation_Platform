# UI/UX Design Rulebook — Havells Sambandh

| Field | Value |
| :--- | :--- |
| **Document Version** | 1.0.0 |
| **Phase** | Phase 02 — UI/UX Design Rulebook |
| **Brand** | Havells Sambandh — Enterprise Dealer Engagement & Automation Platform |
| **UI Stack** | React + TypeScript + Tailwind CSS + Lucide React Icons |
| **Font Family** | Poppins (Google Fonts / Self-hosted WOFF2) |
| **Last Updated** | 2026-11-23 |

---

## 1. Design Philosophy & Brand Direction

**Havells Sambandh** must project **premium corporate reliability, clarity, and operational precision**. Every screen — from the internal enterprise admin portal to the zero-login public dealer confirmation form — follows a unified Havells Red & White visual language.

### Core Principles
1. **Clean Corporate Hierarchy:** Generous whitespace, crisp white card surfaces (`#FFFFFF`) over subtle light-gray canvases (`#F8F8F8`), and disciplined typographic scale.
2. **Purposeful Havells Red:** Primary Red (`#D71920`) is reserved for primary CTAs, active navigation indicators, brand wordmark accents, and key highlights — never overused as noisy full-screen backgrounds.
3. **Zero-Friction Public Experience:** The Dealer Date Confirmation Form is mobile-first, scannable in under 5 seconds, free of clutter, and strictly limited to the 4 approved fields.
4. **Immediate Feedback:** Every interactive control exposes unmistakable hover, focus, active, loading, disabled, and validation error states.
5. **Accessibility First (WCAG 2.1 AA):** High-contrast text (`>= 4.5:1`), visible keyboard focus rings, semantic HTML landmarks, and screen-reader-friendly form labels/errors.

---

## 2. Color System & Semantic Tokens

### 2.1 Brand & Neutral Palette (Mandatory)

| Token Name | Hex | Tailwind Token | Usage |
| :--- | :--- | :--- | :--- |
| **Primary Red** | `#D71920` | `brand-primary` | Primary buttons, active nav bar accent, brand header accent, primary links, focus highlights |
| **Dark Red** | `#B5121B` | `brand-dark` | Primary button hover/active state, pressed accents |
| **Soft Red Tint** | `#FEF2F2` | `brand-tint` | Active sidebar item background, subtle brand callout surface |
| **White** | `#FFFFFF` | `surface-white` | Cards, modals, tables, inputs, sidebar, topbar |
| **Background** | `#F8F8F8` | `surface-bg` | Page canvas background (internal portal & public form shell) |
| **Subtle Surface** | `#F3F4F6` | `surface-muted` | Table headers, disabled inputs, hover row backgrounds |
| **Primary Text** | `#222222` | `text-primary` | Headings, primary data values, form labels |
| **Secondary Text** | `#6B7280` | `text-secondary` | Helper text, subtitles, table metadata, placeholders |
| **Border** | `#E5E7EB` | `border-default` | Card borders, input borders, dividers, table row separators |

### 2.2 Semantic Status Colors

| Status | Main Hex | Tint Background | Border Hex | Usage |
| :--- | :--- | :--- | :--- | :--- |
| **Success** | `#16A34A` | `#F0FDF4` | `#BBF7D0` | Confirmed bookings, active status badges, success toast/screen |
| **Warning** | `#F59E0B` | `#FFFBEB` | `#FDE68A` | Pending confirmations, expiring soon links, partial capacity warnings |
| **Error** | `#DC2626` | `#FEF2F2` | `#FECACA` | Validation errors, expired/deactivated links, destructive actions, failed imports |
| **Info / Neutral** | `#374151` | `#F3F4F6` | `#D1D5DB` | Draft campaigns, shared-not-used neutral badges, informational tags |

### 2.3 Contrast & Accessibility Rules
- White text (`#FFFFFF`) on Primary Red (`#D71920`) meets WCAG AA for normal/large UI text and buttons (`5.14:1`).
- Primary Text (`#222222`) on White (`#FFFFFF`) achieves `15.9:1` (AAA).
- Secondary Text (`#6B7280`) on White (`#FFFFFF`) achieves `4.83:1` (AA).
- Never place Secondary Text (`#6B7280`) on muted gray (`#F3F4F6`) for critical instructions — use `#4B5563` or `#222222`.

---

## 3. Typography System (`Poppins`)

| Style | Font Weight | Size (Desktop) | Line Height | Letter Spacing | Usage |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Display / Page Title** | Bold (700) | `24px` (`1.5rem`) | `32px` (`1.33`) | `-0.015em` | Main page headings, Public Form title |
| **Section Heading (H2)** | SemiBold (600) | `18px` (`1.125rem`) | `26px` (`1.44`) | `-0.01em` | Card headers, modal titles, chart titles |
| **Subheading (H3)** | SemiBold (600) | `16px` (`1rem`) | `24px` (`1.5`) | `0` | Form group headings, sub-panels |
| **KPI Metric Value** | Bold (700) | `28px` (`1.75rem`) | `34px` (`1.21`) | `-0.02em` | Dashboard KPI numbers (`tabular-nums`) |
| **Body Default** | Regular (400) | `14px` (`0.875rem`) | `22px` (`1.57`) | `0` | Table cells, descriptions, form inputs |
| **Body Small / Meta** | Regular (400) | `12px` (`0.75rem`) | `18px` (`1.5`) | `0.01em` | Helper text, timestamps, validation errors, badges |
| **Button / Nav Label** | Medium (500) | `14px` (`0.875rem`) | `20px` (`1.43`) | `0.005em` | Buttons, tabs, sidebar links |
| **Table Header** | SemiBold (600) | `12px` (`0.75rem`) | `16px` (`1.33`) | `0.04em` | Uppercase column headers (`text-secondary`) |

**Numeric Alignment Rule:** All KPI numbers, counts, dates, times, dealer codes, and mobile numbers MUST use `font-variant-numeric: tabular-nums` (`tabular-nums` in Tailwind) so columns align cleanly.

---

## 4. Spacing, Layout Grid & Elevation

### 4.1 Spacing Scale (4px Base Unit)
- `4px` (`1`): Tight inline icon-to-label micro gaps
- `8px` (`2`): Standard icon-to-text gap, compact badge padding
- `12px` (`3`): Input vertical padding, compact list item gap
- `16px` (`4`): Standard form field spacing, mobile page padding
- `20px` (`5`): Card internal padding (compact)
- `24px` (`6`): Card internal padding (standard), grid gutter, desktop page padding
- `32px` (`8`): Major section separation

### 4.2 Border Radius
- **Inputs & Buttons:** `8px` (`rounded-lg`)
- **Cards & Tables:** `12px` (`rounded-xl`)
- **Modals & Public Form Container:** `16px` (`rounded-2xl`)
- **Status Pills / Badges:** `9999px` (`rounded-full`)

### 4.3 Elevation & Shadows (Soft Corporate)
- **Card Default (`shadow-card`):** `0 1px 3px rgba(16, 24, 40, 0.06), 0 1px 2px rgba(16, 24, 40, 0.04)` + `1px solid #E5E7EB`
- **Card Hover / Elevated (`shadow-card-hover`):** `0 4px 12px rgba(16, 24, 40, 0.08)`
- **Dropdown / Popover (`shadow-dropdown`):** `0 10px 24px rgba(16, 24, 40, 0.10)`
- **Modal / Public Form Card (`shadow-modal`):** `0 20px 40px rgba(16, 24, 40, 0.12)`

---

## 5. Responsive Breakpoints & Layout Shells

| Breakpoint | Min Width | Tailwind Prefix | Layout Behavior |
| :--- | :--- | :--- | :--- |
| **Mobile** | `320px` | default | Single-column stack; collapsible slide-over sidebar drawer; full-width primary buttons; horizontally scrollable tables or stacked card view |
| **Tablet** | `768px` | `md:` | 2-column KPI grid; collapsible sidebar drawer; 2-column modal forms |
| **Laptop** | `1024px` | `lg:` | Persistent left sidebar (`248px` wide); 4-column KPI grid; side-by-side analytics charts |
| **Desktop** | `1440px` | `xl:` / `2xl:` | Persistent left sidebar (`260px` wide); max content container `1440px` centered; comfortable spacious tables without horizontal scrolling |

### 5.1 Internal Portal Shell (`AdminLayout`)
- **Left Sidebar (`#FFFFFF`, right border `#E5E7EB`):**
  - Top: Havells Sambandh brand lockup (`HAVELLS` bold red `#D71920` + `Sambandh` medium `#222222`).
  - Body: Permission-filtered navigation links with minimal `18px` Lucide icons (`strokeWidth={1.75}`). Active item uses `#FEF2F2` fill, `#D71920` text/icon, and a `3px` left red indicator bar.
  - Footer: Compact logged-in user badge (Name + Role) and Logout button.
- **Top Header Bar (`64px` height, `#FFFFFF`, bottom border `#E5E7EB`):**
  - Left: Mobile hamburger toggle (`< 1024px`) + Breadcrumb / Current Page Title.
  - Right: Quick campaign/environment badge, Profile dropdown (Profile & Settings, Change Password, Logout).
- **Main Content Area (`#F8F8F8` canvas):**
  - `24px` padding on desktop (`16px` on mobile), consistent Page Header (Title + Subtitle + Primary CTA button on the right), Filter Bar, and Card/Table content.

### 5.2 Public Confirmation Shell (`PublicLayout`)
- Full-height `#F8F8F8` canvas with a subtle top Havells Red accent bar (`4px` `#D71920`).
- Centered white card (`max-width: 480px` on desktop, full-width with `16px` margin on mobile, `rounded-2xl`, `shadow-modal`).
- Dedicated branded header (`HAVELLS Sambandh` / `Dealer Engagement Program`), clean form body, and minimal corporate footer (`© Havells India Ltd. • Dealer Engagement Program`).
- Zero internal navigation links, zero login prompts, zero distracting banners.

---

## 6. Iconography, Motion & Interaction Rules

### 6.1 Iconography
- Library: **Lucide React** exclusively.
- Stroke width: `1.75` for navigation and cards; `2.0` for small inline status icons.
- Sizes: `16px` (inline button/input icons), `18px` (sidebar nav), `20px` (KPI card icons), `48px` (success/error state hero icons).
- Keep icon usage minimal — never decorate every text label with an icon.

### 6.2 Motion & Transitions
- Standard hover/focus transition: `150ms ease-in-out` (`transition-colors duration-150`).
- Modal/drawer entrance: `200ms ease-out` fade + subtle scale/slide.
- Respect `prefers-reduced-motion: reduce`.

### 6.3 Form Validation & Error Presentation
- **Required fields:** Marked with a subtle red asterisk (`*`) in `#D71920`.
- **Inline errors:** Displayed immediately below the offending input in `12px` `#DC2626` with a `14px` `AlertCircle` icon; input border changes to `#DC2626` with soft red focus ring (`ring-red-100`).
- **Form-level errors (e.g., API rejection, slot taken):** Displayed in a dismissible top-of-form Alert Banner (`#FEF2F2` background, `#FECACA` border, `#DC2626` text).
- **Double-submit prevention:** Every form submit button transitions to a disabled loading state with an inline spinner during in-flight API calls.

---

## 7. Tailwind Configuration Reference

These exact design tokens will be configured in `frontend/tailwind.config.ts` during Phase 03:

```ts
theme: {
  extend: {
    colors: {
      brand: {
        primary: '#D71920',
        dark: '#B5121B',
        tint: '#FEF2F2',
      },
      surface: {
        white: '#FFFFFF',
        bg: '#F8F8F8',
        muted: '#F3F4F6',
      },
      ink: {
        primary: '#222222',
        secondary: '#6B7280',
      },
      line: {
        DEFAULT: '#E5E7EB',
      },
      status: {
        success: '#16A34A',
        warning: '#F59E0B',
        error: '#DC2626',
      },
    },
    fontFamily: {
      sans: ['Poppins', 'system-ui', '-apple-system', 'sans-serif'],
    },
  },
}
```
