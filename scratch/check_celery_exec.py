import os, sys, django
sys.path.append('c:/personal/projects/viralOps/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viralops.settings')
django.setup()

from django.conf import settings
from celery import Celery

print("DJANGO_ENV:", os.getenv("DJANGO_ENV"))
print("DJANGO_SETTINGS_MODULE:", os.getenv("DJANGO_SETTINGS_MODULE"))
print("CELERY_TASK_ALWAYS_EAGER:", getattr(settings, "CELERY_TASK_ALWAYS_EAGER", None))
print("CELERY_BROKER_URL:", getattr(settings, "CELERY_BROKER_URL", None))
print("CELERY_RESULT_BACKEND:", getattr(settings, "CELERY_RESULT_BACKEND", None))

app = Celery('viralops')
app.config_from_object('django.conf:settings', namespace='CELERY')

try:
    inspect = app.control.inspect()
    print("Ping workers:")
    ping_result = inspect.ping()
    print("Ping:", ping_result)
    
    if ping_result:
        print("Worker online? YES")
        print("Worker count:", len(ping_result))
        print("Active tasks:", inspect.active())
        print("Reserved tasks:", inspect.reserved())
        print("Scheduled tasks:", inspect.scheduled())
    else:
        print("Worker online? NO")
        print("Worker count: 0")
        print("Active tasks: None")
        print("Reserved tasks: None")
        print("Scheduled tasks: None")
except Exception as e:
    print("Celery control inspect error:", e)
    print("Worker online? NO")
    print("Worker count: 0")
    print("Active tasks: None")
    print("Reserved tasks: None")
    print("Scheduled tasks: None")
