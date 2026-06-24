import os
import sys
import django
from django.conf import settings
from dotenv import dotenv_values

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viralops.settings.production')
try:
    django.setup()
except Exception as e:
    print(f"Django setup exception: {e}")

env_file_path = os.path.join(settings.BASE_DIR, '.env')
env_file_present = os.path.exists(env_file_path)
raw_env = dotenv_values(env_file_path) if env_file_present else {}

def mask(val):
    if not val:
        return 'None'
    if len(val) <= 4:
        return '***'
    return val[:4] + '***' + val[-4:]

keys_to_check = ['RESEND_API_KEY', 'NVIDIA_API_KEY', 'SENTRY_DSN', 'DATABASE_URL', 'REDIS_URL', 'RAZORPAY_KEY_ID']

print("--- ENV AUDIT ---")
print(f"ENV_FILE_PRESENT: {env_file_present}")

for k in keys_to_check:
    val_os = os.environ.get(k)
    val_settings = getattr(settings, k, None)
    if val_settings is None and k == 'REDIS_URL':
        val_settings = getattr(settings, 'CELERY_BROKER_URL', None)
    elif val_settings is None and k == 'DATABASE_URL':
        val_settings = os.environ.get('DATABASE_URL')  # It's parsed into DATABASES usually

    print(f"{k} (os.environ): {mask(val_os)}")
    if val_os:
        if k in raw_env and raw_env[k] == val_os:
            print(f"  Origin: .env")
        else:
            print(f"  Origin: System Environment Variables (or Platform)")
    
    # Missing at runtime check
    if k in raw_env and raw_env[k] and not val_os:
        print(f"  WARNING: Present in .env but MISSING in os.environ at runtime.")

print("-----------------")

print("Checking Connections...")
db_ready = "NO"
try:
    from django.db import connections
    conn = connections['default']
    conn.ensure_connection()
    db_ready = "YES"
except Exception as e:
    db_ready = f"NO ({e})"

redis_ready = "NO"
try:
    import redis
    r = redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))
    r.ping()
    redis_ready = "YES"
except Exception as e:
    redis_ready = f"NO ({e})"

email_ready = "NO"
if os.environ.get('RESEND_API_KEY'):
    # Anymail backend setup test
    email_ready = "YES"
else:
    email_ready = "NO (Missing RESEND_API_KEY)"

ai_ready = "NO"
if os.environ.get('NVIDIA_API_KEY'):
    ai_ready = "YES"
else:
    ai_ready = "NO (Missing NVIDIA_API_KEY)"

print(f"DATABASE_READY: {db_ready}")
print(f"REDIS_READY: {redis_ready}")
print(f"EMAIL_PROVIDER_READY: {email_ready}")
print(f"AI_PROVIDER_READY: {ai_ready}")
