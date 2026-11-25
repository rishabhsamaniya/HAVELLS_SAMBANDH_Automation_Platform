# Production Deployment Guide — Havells Sambandh

| Field | Value |
| :--- | :--- |
| **Document Version** | 1.0.0 |
| **Target Platform** | Render (Web Service + Static Site + Managed PostgreSQL + Worker + Redis) |
| **Health Check** | `GET /api/v1/health/` |

---

## 1. Architecture Overview
- **Frontend:** Render Static Site serving `frontend/dist` with SPA rewrite (`/* → /index.html`).
- **Backend API:** Render Python Web Service running Gunicorn (`config.wsgi:application`) with `DJANGO_SETTINGS_MODULE=config.settings.production` and WhiteNoise static serving.
- **Database:** Render Managed PostgreSQL (`DATABASE_URL` injected automatically).
- **Worker & Scheduler:** Render Background Worker running `celery -A config worker --beat -l info` connected to Managed Redis (`CELERY_BROKER_URL`).

---

## 2. Deployment Steps (Render Blueprint)

1. Push the repository to GitHub (verify `.env` is NOT committed).
2. In Render Dashboard → **New + → Blueprint**, connect your repository. Render detects [render.yaml](../render.yaml).
3. Configure required production environment variables on `havells-sambandh-api`:
   - `DJANGO_ALLOWED_HOSTS=api.yourdomain.com`
   - `FRONTEND_BASE_URL=https://app.yourdomain.com`
   - `CORS_ALLOWED_ORIGINS=https://app.yourdomain.com`
   - `CSRF_TRUSTED_ORIGINS=https://app.yourdomain.com`
   - `AUTH_COOKIE_SECURE=True`
   - `AUTH_COOKIE_SAMESITE=None` (if frontend and API are on different subdomains over HTTPS)
4. Configure on `havells-sambandh-frontend`:
   - `VITE_API_BASE_URL=https://api.yourdomain.com/api/v1`
5. Trigger deploy. `scripts/build_backend.sh` automatically runs `collectstatic`, `migrate`, and `seed_rbac`.
6. Create the initial Super Admin via Render Shell:
   ```bash
   cd backend
   python manage.py createsuperuser
   ```
7. Verify `GET https://api.yourdomain.com/api/v1/health/` returns `200 OK`.

---

## 3. PostgreSQL Backup & Restore Strategy

### Automated Backups
Enable Render PostgreSQL daily automated backups and point-in-time recovery (PITR) on production plans.

### Manual Backup (`pg_dump`)
```bash
pg_dump "$DATABASE_URL" --format=custom --no-owner --file="havells_sambandh_$(date +%Y%m%d_%H%M).dump"
```

### Restore (`pg_restore`)
```bash
pg_restore --clean --if-exists --no-owner --dbname="$DATABASE_URL" havells_sambandh_YYYYMMDD_HHMM.dump
```
