"""Development settings for Havells Sambandh."""
import os

from .base import *  # noqa: F401, F403

DEBUG = True
AUTH_COOKIE_SECURE = False

# PostgreSQL is the primary development database.
# Set USE_LOCAL_SQLITE=True in .env only if PostgreSQL is not installed locally.
if os.getenv("USE_LOCAL_SQLITE", "False").lower() == "true":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "dev_db.sqlite3",  # noqa: F405
        }
    }
