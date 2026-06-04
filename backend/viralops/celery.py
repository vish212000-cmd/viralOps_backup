import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viralops.settings')

app = Celery('viralops')

# Read config from Django settings, namespace 'CELERY' means
# all celery-related configs must be prefixed with 'CELERY_'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Expose worker metrics to Prometheus registry
from prometheus_client import REGISTRY

