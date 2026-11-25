# Havells Sambandh — Enterprise Dealer Engagement & Automation Platform

**Havells Sambandh** is a production-ready, API-first Dealer Engagement & Experience Management Platform built with **Django 5 + Django REST Framework**, **React 18 + TypeScript + Tailwind CSS**, **PostgreSQL**, and **Celery + Redis**.

---

## Key Features (v1.0 — Dealer Date Confirmation System)
- **Mobile + Password Authentication:** 10-digit Indian mobile login, JWT access tokens, `HttpOnly` rotating refresh cookies, logout blacklisting, failed-login lockout, change/forgot password.
- **Dynamic Database-Driven RBAC:** 5 seeded roles (`Super Admin`, `Admin`, `Management`, `RM`, `MIS Executive`), 38 granular module × action permissions, centralized `PermissionService`, and strict RM territory isolation.
- **Dealer Management:** Add/edit/deactivate/search/filter dealers, confirmation history, validated `.xlsx` bulk import (magic-byte check, row-level errors, zero silent overwrites), and formula-safe Excel/CSV export.
- **Unique Confirmation Links:** 256-bit cryptographic tokens stored only as SHA-256 hashes, `allowed_month` locking, one-time copyable URL + WhatsApp/SMS share message, mark-shared, deactivate, and auto-revocation.
- **Public Dealer Confirmation Form (Zero Login):** Strictly 4 fields (`Dealer Code`, `Mobile Number`, `Preferred Date`, `Preferred Time Slot`), same-month future-only date rule (`Asia/Kolkata`), dynamic 1-hour AM/PM slots, atomic `SELECT FOR UPDATE` booking, and exact approved success screen.
- **Scheduling Engine:** Configurable operating hours, slot capacities, holidays, block/unblock slots, manual booking, and authorized RM/Admin rescheduling & cancellation with immutable history.
- **Live Admin Dashboard & 8 Reports:** 8 real-time KPIs, 7 analytics datasets, and 8 RBAC-scoped reports exportable to `.xlsx` and `.csv`.
- **Notifications, Automation & Audit Logs:** Pluggable WhatsApp/SMS/Email/In-App provider interfaces, Celery Beat link-expiry sweeps, and immutable secret-redacted audit trails.

---

## Tech Stack
- **Backend:** Python 3.12+, Django 5.2, Django REST Framework 3.16, Simple JWT, `django-filter`, `drf-spectacular`, PostgreSQL (`psycopg`), Celery + Redis, OpenPyXL, Pandas, Gunicorn, WhiteNoise.
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS (Havells Red `#D71920` & White, Poppins), React Router, TanStack Query, React Hook Form + Zod, Axios, Lucide React, Recharts.
- **Testing:** Pytest + `pytest-django` (41 tests) · Vitest + React Testing Library (3 tests).

---

## Local Installation & Running

### 1. Environment Configuration
```bash
cp .env.example .env
```
- **With PostgreSQL (Recommended):** Set `DATABASE_URL=postgres://postgres:postgres@localhost:5432/havells_sambandh` in `.env`.
- **Quick Local Run without PostgreSQL installed:** Add `USE_LOCAL_SQLITE=True` to `.env`.

### 2. Backend Setup & Run
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements/development.txt

python manage.py migrate
python manage.py seed_rbac
python manage.py shell -c "from apps.scheduling.services import generate_time_slots_from_config; generate_time_slots_from_config()"
python manage.py createsuperuser

# Start Django API server on http://localhost:8000
python manage.py runserver
```

### 3. Frontend Setup & Run (New Terminal)
```bash
cd frontend
npm install
npm run dev
# Opens http://localhost:5173 (proxies /api to http://localhost:8000)
```

### 4. Optional: Celery Worker & Beat (Requires Redis)
```bash
cd backend
source .venv/bin/activate
celery -A config worker --beat -l info
```

---

## Testing Commands
```bash
# Backend (41 automated unit, integration, RBAC, security & E2E tests)
cd backend && .venv/bin/pytest -v tests/

# Frontend (Vitest + TypeScript strict check + Vite production build)
cd frontend && npm test && npm run typecheck && npm run build
```

---

## Interactive API Docs (When Backend is Running)
- **Swagger UI:** `http://localhost:8000/api/v1/docs/`
- **ReDoc:** `http://localhost:8000/api/v1/redoc/`
- **Health Check:** `http://localhost:8000/api/v1/health/`

---

## Documentation Index
- [PRD](docs/PRD.md) · [Feature List](docs/FEATURE_LIST.md) · [Business Rules](docs/BUSINESS_RULES.md)
- [UI Rulebook](docs/UI_RULEBOOK.md) · [Component Library](docs/COMPONENT_LIBRARY.md) · [Screen Specifications](docs/SCREEN_SPECIFICATIONS.md)
- [System Architecture](docs/ARCHITECTURE.md) · [Database Schema](docs/DATABASE_SCHEMA.md) · [RBAC Matrix](docs/RBAC_MATRIX.md)
- [API Documentation](docs/API_DOCUMENTATION.md) · [Testing Guide](docs/TESTING_GUIDE.md) · [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)
- [Changelog](docs/CHANGELOG.md) · [Phase Progress](docs/PHASE_PROGRESS.md)
