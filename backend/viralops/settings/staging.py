from .production import *
import os
import sentry_sdk
import logging

# Staging Environment Configuration
DEBUG = False
SENTRY_ENV = 'staging'

# Overwrite Sentry Tracing configuration with staging sample rate (0.05)
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
        traces_sample_rate=0.05,  # Staging trace sample rate
        profiles_sample_rate=0.05,
        send_default_pii=True,
        before_send_transaction=lambda event, hint: None 
            if event.get('transaction') in [
                '/health/', '/healthz/', '/ready/', 
                '/metrics/', '/prometheus/'
            ] else event,
    )

# (Console email backend override removed for production/staging parity)

# Block startup on missing keys
BLOCK_STARTUP_ON_MISSING_SECRETS = 1

import dj_database_url
import ssl

# Database configuration is strictly inherited from production.py
# which enforces Neon PostgreSQL via DATABASE_URL.

# Upstash Redis configuration for Celery (Requires SSL without cert validation)
if CELERY_BROKER_URL.startswith('rediss://'):
    CELERY_REDIS_BACKEND_USE_SSL = {"ssl_cert_reqs": ssl.CERT_NONE}
    CELERY_BROKER_USE_SSL = {"ssl_cert_reqs": ssl.CERT_NONE}

# Add WhiteNoise to middleware for serving static files on Render
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
