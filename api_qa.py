import requests
import json
import uuid

BASE_URL = "https://viralops-web.onrender.com"

report = {
    "auth": {},
    "api": {},
    "infrastructure": {}
}

print("Running API QA...")

# --- PHASE 5: API QA ---
# 1. Health
print("Testing Health Endpoint...")
try:
    res = requests.get(f"{BASE_URL}/healthz/", timeout=60)
    report["api"]["health"] = {"status": res.status_code, "body": res.text}
except Exception as e:
    report["api"]["health"] = {"error": str(e)}

# --- PHASE 4: AUTHENTICATION QA ---
# 2. Signup
print("Testing Signup...")
email = f"qa_audit_{uuid.uuid4().hex[:8]}@example.com"
password = "TestPassword123!"

try:
    res = requests.post(f"{BASE_URL}/api/auth/register/", json={
        "username": email,
        "email": email,
        "password": password,
        "first_name": "QA",
        "last_name": "Audit"
    }, timeout=60)
    report["auth"]["signup"] = {"status": res.status_code, "body": res.text}
except Exception as e:
    report["auth"]["signup"] = {"error": str(e)}

# 3. Login
print("Testing Login...")
token = None
refresh_token = None
try:
    res = requests.post(f"{BASE_URL}/api/auth/login/", json={
        "username": email,
        "password": password
    }, timeout=60)
    report["auth"]["login"] = {"status": res.status_code, "body": res.text}
    if res.status_code == 200:
        data = res.json()
        token = data.get("access")
        refresh_token = data.get("refresh")
except Exception as e:
    report["auth"]["login"] = {"error": str(e)}

# 4. Token Refresh
print("Testing Token Refresh...")
if refresh_token:
    try:
        res = requests.post(f"{BASE_URL}/api/auth/refresh/", json={
            "refresh": refresh_token
        }, timeout=60)
        report["auth"]["refresh"] = {"status": res.status_code, "body": res.text}
    except Exception as e:
        report["auth"]["refresh"] = {"error": str(e)}

# --- PHASE 5: API QA (Protected Endpoints) ---
if token:
    headers = {"Authorization": f"Bearer {token}"}
    
    # Projects
    print("Testing Projects API...")
    try:
        res = requests.get(f"{BASE_URL}/api/orgs/default/projects/", headers=headers, timeout=60)
        report["api"]["projects"] = {"status": res.status_code, "body": res.text}
    except Exception as e:
        report["api"]["projects"] = {"error": str(e)}
        
    # Billing
    print("Testing Billing API...")
    try:
        res = requests.get(f"{BASE_URL}/api/billing/plans/", headers=headers, timeout=10)
        report["api"]["billing_plans"] = {"status": res.status_code, "body": res.text}
    except Exception as e:
        report["api"]["billing_plans"] = {"error": str(e)}

with open('C:/Users/TCCSPL/.gemini/antigravity/brain/afc95b85-e151-49f3-acd4-9fff6b88a2ad/api_results.json', 'w') as f:
    json.dump(report, f, indent=2)

print("API QA Complete.")
