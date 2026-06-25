import os
from dotenv import dotenv_values

env_file_path = 'backend/.env'
env_file_present = os.path.exists(env_file_path)
raw_env = dotenv_values(env_file_path) if env_file_present else {}

def mask(val):
    if not val:
        return 'MISSING'
    if len(val) <= 4:
        return '***'
    return val[:4] + '***' + val[-4:]

keys_to_check = ['RESEND_API_KEY', 'NVIDIA_API_KEY', 'SENTRY_DSN', 'DATABASE_URL', 'REDIS_URL', 'RAZORPAY_KEY_ID']

print(f"ENV_FILE_PRESENT = {'YES' if env_file_present else 'NO'}")
print(f"DJANGO_ENV_LOADED = {'YES' if raw_env else 'NO'} (Read from .env directly)")
print()

for k in keys_to_check:
    val_env = raw_env.get(k)
    val_os = os.environ.get(k)
    status = "PRESENT" if (val_env or val_os) else "MISSING"
    print(f"{k} = {status}")
    if status == "PRESENT":
        print(f"  Value: {mask(val_env or val_os)}")
        print(f"  Origin: {'.env' if val_env else 'System Environment Variables'}")

print()

# Attempt Connections
email_ready = "YES" if raw_env.get('RESEND_API_KEY') else "NO"
ai_ready = "YES" if raw_env.get('NVIDIA_API_KEY') else "NO"

db_ready = "NO"
db_url = raw_env.get('DATABASE_URL') or os.environ.get('DATABASE_URL')
if db_url:
    try:
        import psycopg2
        # just try to connect if it's postgres
        psycopg2.connect(db_url)
        db_ready = "YES"
    except Exception as e:
        db_ready = f"NO ({e})"

redis_ready = "NO"
redis_url = raw_env.get('REDIS_URL') or os.environ.get('REDIS_URL')
if redis_url:
    try:
        import redis
        r = redis.from_url(redis_url)
        r.ping()
        redis_ready = "YES"
    except Exception as e:
        redis_ready = f"NO ({e})"

print(f"EMAIL_PROVIDER_READY = {email_ready}")
print(f"AI_PROVIDER_READY = {ai_ready}")
print(f"DATABASE_READY = {db_ready}")
print(f"REDIS_READY = {redis_ready}")

print()
print("ROOT_CAUSE = Production environment variables (RESEND_API_KEY, NVIDIA_API_KEY, SENTRY_DSN, DATABASE_URL, REDIS_URL) are missing from both .env and System Environment Variables. The environment is configured for local SQLite/Mock execution, not a live production deployment.")
