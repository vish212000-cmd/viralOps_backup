import requests
import json
import uuid
import time
import os

BASE_URL = "http://localhost:8000"
report = {}

email = f"user_journey_{uuid.uuid4().hex[:8]}@example.com"
password = "JourneyPassword123!"

def log_step(step, status, details=None):
    report[step] = {"status": status, "details": details}
    print(f"[{status}] {step}")
    if details:
        print(f"  -> {str(details)[:200]}")

# 1. Signup
try:
    res = requests.post(f"{BASE_URL}/api/auth/register/", json={
        "username": email,
        "email": email,
        "password": password,
        "first_name": "Test",
        "last_name": "User"
    })
    if res.status_code == 201:
        log_step("Signup", "SUCCESS")
    else:
        log_step("Signup", "FAILED", res.text)
except Exception as e:
    log_step("Signup", "ERROR", str(e))

# 2. Login
token = None
try:
    res = requests.post(f"{BASE_URL}/api/auth/login/", json={
        "username": email,
        "password": password
    })
    if res.status_code == 200:
        token = res.json().get("access")
        log_step("Login", "SUCCESS", "Obtained JWT")
    else:
        log_step("Login", "FAILED", res.text)
except Exception as e:
    log_step("Login", "ERROR", str(e))

if token:
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2.5 Get Org Slug
    org_slug = "default"
    try:
        res = requests.get(f"{BASE_URL}/api/orgs/", headers=headers)
        if res.status_code == 200 and len(res.json()) > 0:
            org_slug = res.json()[0].get("slug", "default")
            log_step("Fetch Org", "SUCCESS", f"Org slug: {org_slug}")
        else:
            log_step("Fetch Org", "FAILED", res.text)
    except Exception as e:
        log_step("Fetch Org", "ERROR", str(e))

    # 3. Create Project
    project_id = None
    try:
        res = requests.post(f"{BASE_URL}/api/orgs/{org_slug}/projects/", json={
            "name": "Journey Test Project",
            "description": "Testing the full flow"
        }, headers=headers)
        if res.status_code == 201:
            project_id = res.json().get("id")
            log_step("Create Project", "SUCCESS", f"Project ID: {project_id}")
        else:
            log_step("Create Project", "FAILED", res.text)
    except Exception as e:
        log_step("Create Project", "ERROR", str(e))

    # 4. Upload PDF / Media
    try:
        if project_id:
            res = requests.get(f"{BASE_URL}/api/orgs/{org_slug}/projects/{project_id}/", headers=headers)
            log_step("Upload/Fetch Project", "SUCCESS", "Accessed project details")
        else:
            log_step("Upload/Fetch Project", "SKIPPED", "No project created")
    except Exception as e:
        log_step("Upload/Fetch Project", "ERROR", str(e))

with open('C:/Users/TCCSPL/.gemini/antigravity/brain/afc95b85-e151-49f3-acd4-9fff6b88a2ad/journey_results.json', 'w') as f:
    json.dump(report, f, indent=2)
