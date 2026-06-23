import os
import sys
import django
import redis
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viralops.settings.local')
django.setup()

from django.conf import settings
from projects.models import Project, SourceInput, ProcessingJob, UsageEvent

print("=== Django / Database Settings ===")
print("DATABASES:", settings.DATABASES)
print("CELERY_BROKER_URL:", getattr(settings, "CELERY_BROKER_URL", None))
print("CELERY_TASK_ALWAYS_EAGER:", getattr(settings, "CELERY_TASK_ALWAYS_EAGER", None))

print("\n=== Active/Stalled Ingestions ===")
# Detailed query of running things
for p in Project.objects.filter(status='PROCESSING'):
    print(f"Project ID: {p.id}, Status: {p.status}, Updated At: {p.updated_at}")
for s in SourceInput.objects.filter(status='PROCESSING'):
    print(f"SourceInput ID: {s.id}, Status: {s.status}, Updated At: {s.updated_at}, Type: {s.type}, URL: {s.source_url}")
for j in ProcessingJob.objects.filter(status='RUNNING'):
    print(f"ProcessingJob ID: {j.id}, Status: {j.status}, Updated At: {j.updated_at}, failing_step: {getattr(j, 'failing_step', None)}, error_log: {j.error_log}")

print("\n=== Inspecting Redis ===")
broker_url = getattr(settings, "CELERY_BROKER_URL", "redis://localhost:6379/0")
print(f"Connecting to Redis at: {broker_url}")
try:
    r = redis.Redis.from_url(broker_url)
    ping = r.ping()
    print("Redis Ping:", ping)
    
    # Queue lengths
    print("Keys in Redis:", r.keys("*"))
    # In Celery, default queue is 'default'
    for key in r.keys("*"):
        key_type = r.type(key).decode('utf-8')
        if key_type == 'list':
            print(f"List Queue Length for {key.decode('utf-8')}: {r.llen(key)}")
        elif key_type == 'string':
            print(f"String key {key.decode('utf-8')}: {r.get(key)}")
        else:
            print(f"Key {key.decode('utf-8')} ({key_type})")
except Exception as e:
    print("Redis Error:", e)

print("\n=== Inspecting Celery ===")
try:
    app = Celery('viralops')
    app.config_from_object('django.conf:settings', namespace='CELERY')
    inspect = app.control.inspect()
    
    print("Inspecting workers...")
    active = inspect.active()
    print("Active Tasks:", active)
    reserved = inspect.reserved()
    print("Reserved Tasks:", reserved)
    scheduled = inspect.scheduled()
    print("Scheduled Tasks:", scheduled)
except Exception as e:
    print("Celery Inspect Error:", e)

