from .base import *
from django.core.exceptions import ImproperlyConfigured

DEBUG = False

import sentry_sdk
import logging

SENTRY_DSN = os.getenv('SENTRY_DSN', '')
SENTRY_RELEASE = os.getenv('SENTRY_RELEASE', 'unknown')  # set from git commit
SENTRY_ENV = os.getenv('SENTRY_ENV', 'production')

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=SENTRY_ENV,
        release=SENTRY_RELEASE,
        integrations=[
            sentry_sdk.integrations.django.DjangoIntegration(),
            sentry_sdk.integrations.celery.CeleryIntegration(
                monitor_beat_tasks=True,
            ),
            sentry_sdk.integrations.logging.LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR,
            ),
        ],
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
        send_default_pii=True,
        # Exclude health check endpoints from tracing
        before_send_transaction=lambda event, hint: None 
            if event.get('transaction') in ['/health/', '/healthz/', '/ready/', '/metrics/', '/prometheus/']
            else event,
    )


# Enforce secure SECRET_KEY on startup
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY or SECRET_KEY == 'django-insecure-060b&@4r83dz(o()bj8a%hyd@x5ar1!(f9#5o)--bgl!g^f_q8':
    raise ImproperlyConfigured("SECRET_KEY environment variable is required and must be secure in production.")


import dj_database_url

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ImproperlyConfigured("DATABASE_URL environment variable is required and must be configured.")

# Neon PostgreSQL Setup
DATABASES = {
    'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=True)
}

# Production Celery Configuration (Redis)
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', os.getenv('REDIS_URL', 'redis://redis:6379/0'))
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', os.getenv('REDIS_URL', 'redis://redis:6379/0'))
CELERY_TASK_ALWAYS_EAGER = False

# Security Hardening parameters
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False') == 'True'

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Content Security Policy (CSP) configurations
CSP_DEFAULT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "fonts.googleapis.com")
CSP_FONT_SRC = ("'self'", "fonts.gstatic.com")
CSP_IMG_SRC = ("'self'", "data:")
CSP_SCRIPT_SRC = ("'self'",)
