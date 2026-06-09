import os
import sys
import django
import urllib.request
import urllib.error
import json

# Setup Django environment
sys.path.append('c:/personal/projects/viralOps/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viralops.settings.staging')
django.setup()

from django.contrib.auth import get_user_model
from django.db import connection
from django.conf import settings

User = get_user_model()

print("--- AUDIT RESULTS ---")

# 1. Database Connectivity
try:
    connection.ensure_connection()
    print("DB_CONNECTIVITY: PASS")
except Exception as e:
    print(f"DB_CONNECTIVITY: FAIL - {e}")

# 2. User Creation via Shell
try:
    test_user = User.objects.create_user(
        email='audit_test@viralops.com',
        password='TestPassword123!',
        first_name='Audit',
        last_name='Test'
    )
    print("USER_CREATION_SHELL: PASS")
    test_user.delete() # Cleanup
except Exception as e:
    print(f"USER_CREATION_SHELL: FAIL - {e}")

# 3. Google OAuth Configuration
client_id = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
client_secret = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')

if client_id and client_secret and client_id != 'mock-id.apps.googleusercontent.com':
    print("OAUTH_CONFIG: PASS")
else:
    print("OAUTH_CONFIG: FAIL - Missing or mock credentials")
    print(f"Found ID: {client_id}")

# 4. HTTP Request to Backend Registration
backend_url = 'https://viralops-web.onrender.com/api/auth/registration/'
try:
    req = urllib.request.Request(backend_url, method='POST', headers={'Content-Type': 'application/json'})
    # Empty payload to see the validation error (should be 400, not 500)
    data = json.dumps({"email": "test@test.com", "password": "TestPassword123!"}).encode('utf-8')
    with urllib.request.urlopen(req, data=data) as response:
        print(f"BACKEND_REGISTRATION: PASS - Status {response.status}")
except urllib.error.HTTPError as e:
    if e.code in [400, 403]: # Expected for validation or missing CSRF depending on setup
        print(f"BACKEND_REGISTRATION: PASS (Validation rejected) - Status {e.code}")
    else:
        print(f"BACKEND_REGISTRATION: FAIL - Status {e.code}")
        print(f"Response: {e.read().decode('utf-8')}")
except Exception as e:
    print(f"BACKEND_REGISTRATION: FAIL - Exception {e}")

# 5. Frontend Check
try:
    urllib.request.urlopen('https://viralops-staging.vercel.app')
    print("FRONTEND_REACHABLE: PASS")
except urllib.error.HTTPError as e:
    print(f"FRONTEND_REACHABLE: FAIL - Status {e.code}")
except Exception as e:
    print(f"FRONTEND_REACHABLE: FAIL - Exception {e}")
