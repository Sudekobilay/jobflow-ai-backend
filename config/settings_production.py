import os

from .settings import *  # noqa: F401,F403

# Production overrides
DEBUG = False

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "http://localhost:80,http://localhost:8000").split(",")
    if origin.strip()
]

# Security
SECRET_KEY = os.getenv("SECRET_KEY", SECRET_KEY)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True") == "True"
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CONTENT_TYPE_NOSNIFF = True

# Static files served by the webserver (nginx) in production
STATIC_ROOT = os.getenv("STATIC_ROOT", os.path.join(BASE_DIR, "staticfiles"))
MEDIA_ROOT = os.getenv("MEDIA_ROOT", os.path.join(BASE_DIR, "media"))

# CORS hardening for production
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "https://app.example.com").split(",")
    if origin.strip()
]
CORS_ALLOW_CREDENTIALS = True

# Sentry configuration
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=float(os.getenv("SENTRY_TRACE_SAMPLE_RATE", "0.1")),
        send_default_pii=True,
    )
