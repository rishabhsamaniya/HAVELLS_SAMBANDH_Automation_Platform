"""Production settings for Havells Sambandh."""
import os

from .base import *  # noqa: F401, F403

DEBUG = False

if SECRET_KEY == "insecure-dev-only-change-in-production":  # noqa: F405
    raise RuntimeError("DJANGO_SECRET_KEY must be set in production.")

# HTTPS & Security Hardening
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True").lower() == "true"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
AUTH_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Restrict DRF renderer to JSON in production (disable browsable API)
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = (  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
)
