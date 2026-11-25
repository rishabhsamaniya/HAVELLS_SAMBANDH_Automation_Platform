"""Test settings for Havells Sambandh."""
import os

from .base import *  # noqa: F401, F403

DEBUG = False

# Use PostgreSQL when TEST_DATABASE_URL is configured; allow local SQLite fallback
# solely when PostgreSQL is unavailable in the local test environment.
if not os.getenv("TEST_DATABASE_URL"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "test_db.sqlite3",  # noqa: F405
        }
    }

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
WHITENOISE_AUTOREFRESH = True
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "anon": "10000/minute",
    "user": "10000/minute",
    "login": "10000/minute",
    "public_confirm_read": "10000/minute",
    "public_confirm_submit": "10000/minute",
}
