import os
import sys
import django
import redis
import psycopg2
from dotenv import dotenv_values
import sentry_sdk

def mask(val):
    if not val:
        return 'None'
    if len(val) <= 4:
        return '***'
    return '***' + val[-4:]

env_path = os.path.join(os.path.dirname(__file__), '.env')
raw_env = dotenv_values(env_path) if os.path.exists(env_path) else {}

# Inject .env into os.environ for Django and tests
for k, v in raw_env.items():
    if v is not None:
        os.environ[k] = v

# Variables
DB_URL = os.environ.get('DATABASE_URL')
REDIS_URL = os.environ.get('REDIS_URL')
NVIDIA_API_KEY = os.environ.get('NVIDIA_API_KEY')
RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')
SENTRY_DSN = os.environ.get('SENTRY_DSN')

report = {
    'DATABASE_CONNECTION': 'FAIL',
    'REDIS_CONNECTION': 'FAIL',
    'NVIDIA_PROVIDER': 'FAIL',
    'EMAIL_PROVIDER': 'FAIL',
    'RAZORPAY_PROVIDER': 'FAIL',
    'SENTRY_PROVIDER': 'FAIL',
    'DJANGO_STARTUP': 'FAIL',
    'ROOT_CAUSE': [],
    'MISSING_VARIABLES': []
}

if not DB_URL: report['MISSING_VARIABLES'].append('DATABASE_URL')
if not REDIS_URL: report['MISSING_VARIABLES'].append('REDIS_URL')
if not NVIDIA_API_KEY: report['MISSING_VARIABLES'].append('NVIDIA_API_KEY')
if not RESEND_API_KEY: report['MISSING_VARIABLES'].append('RESEND_API_KEY')
if not RAZORPAY_KEY_ID: report['MISSING_VARIABLES'].append('RAZORPAY_KEY_ID')
if not SENTRY_DSN: report['MISSING_VARIABLES'].append('SENTRY_DSN')

# 1. DB Test
try:
    if DB_URL:
        # DB_URL is expected to be a psycopg2 compatible URI
        conn = psycopg2.connect(DB_URL)
        conn.close()
        report['DATABASE_CONNECTION'] = 'PASS'
    else:
        report['ROOT_CAUSE'].append('DB_URL missing')
except Exception as e:
    report['ROOT_CAUSE'].append(f"DB Error: {e}")

# 2. Redis Test
try:
    if REDIS_URL:
        r = redis.from_url(REDIS_URL)
        r.ping()
        report['REDIS_CONNECTION'] = 'PASS'
    else:
        report['ROOT_CAUSE'].append('REDIS_URL missing')
except Exception as e:
    report['ROOT_CAUSE'].append(f"Redis Error: {e}")

# 3. NVIDIA Test
if NVIDIA_API_KEY and NVIDIA_API_KEY.startswith('nvapi-'):
    report['NVIDIA_PROVIDER'] = 'PASS'
else:
    if not NVIDIA_API_KEY:
        report['ROOT_CAUSE'].append('NVIDIA API KEY missing')
    else:
        report['ROOT_CAUSE'].append('NVIDIA API KEY invalid format')

# 4. Email Provider (Resend)
if RESEND_API_KEY and RESEND_API_KEY.startswith('re_'):
    report['EMAIL_PROVIDER'] = 'PASS'
else:
    report['ROOT_CAUSE'].append('RESEND_API_KEY missing or invalid format')

# 5. Razorpay
if RAZORPAY_KEY_ID and RAZORPAY_KEY_ID.startswith('rzp_'):
    report['RAZORPAY_PROVIDER'] = 'PASS'
else:
    report['ROOT_CAUSE'].append('RAZORPAY_KEY_ID missing or invalid format')

# 6. Sentry
if SENTRY_DSN and "sentry.io" in SENTRY_DSN:
    report['SENTRY_PROVIDER'] = 'PASS'
else:
    report['ROOT_CAUSE'].append('SENTRY_DSN missing or invalid')

# 7. Django Startup
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viralops.settings.production')
    # Use Neon DB url setting for Django since we injected it
    django.setup()
    report['DJANGO_STARTUP'] = 'PASS'
except Exception as e:
    report['ROOT_CAUSE'].append(f"Django Startup Error: {e}")

all_pass = all(v == 'PASS' for k, v in report.items() if '_CONNECTION' in k or '_PROVIDER' in k or 'DJANGO_STARTUP' in k)
env_complete = len(report['MISSING_VARIABLES']) == 0

print(f"ENV_UPDATE_COMPLETE = {'YES' if env_complete else 'NO'}")
print()
print(f"DATABASE_CONNECTION = {report['DATABASE_CONNECTION']}")
print(f"REDIS_CONNECTION = {report['REDIS_CONNECTION']}")
print(f"NVIDIA_PROVIDER = {report['NVIDIA_PROVIDER']}")
print(f"EMAIL_PROVIDER = {report['EMAIL_PROVIDER']}")
print(f"RAZORPAY_PROVIDER = {report['RAZORPAY_PROVIDER']}")
print(f"SENTRY_PROVIDER = {report['SENTRY_PROVIDER']}")
print()
print(f"DJANGO_STARTUP = {report['DJANGO_STARTUP']}")
print()
if report['ROOT_CAUSE']:
    print(f"ROOT_CAUSE = {'; '.join(report['ROOT_CAUSE'])}")
if report['MISSING_VARIABLES']:
    print(f"MISSING_VARIABLES = {', '.join(report['MISSING_VARIABLES'])}")
print()
print(f"FINAL_STATUS = {'READY' if all_pass else 'NOT_READY'}")
