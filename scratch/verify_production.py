import os
import time
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"

def run_test():
    print("Starting e2e test...")
    username = f"e2e_user_{int(time.time())}"
    email = f"{username}@example.com"
    password = "SecurePassword123!"

    print(f"1. Registering user {username}...")
    reg_res = requests.post(f"{BASE_URL}/auth/register/", json={
        "username": username,
        "email": email,
        "password": password
    })
    
    if reg_res.status_code not in [200, 201]:
        print("Registration failed:", reg_res.status_code, reg_res.text)
        return
        
    token = reg_res.json().get("access")
    print(f"Got access token: {token[:10]}...")
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    print("2. Fetching workspaces...")
    orgs_res = requests.get(f"{BASE_URL}/workspaces/", headers=headers)
    orgs = orgs_res.json()
    if len(orgs) == 0:
        c_org_res = requests.post(f"{BASE_URL}/workspaces/", json={"name": "Test Org", "slug": f"test-org-{int(time.time())}"}, headers=headers)
        org = c_org_res.json()
    else:
        org = orgs[0]
    
    org_slug = org.get('slug')
    print(f"Using org_slug: {org_slug}")

    print("3. Creating project...")
    proj_res = requests.post(f"{BASE_URL}/orgs/{org_slug}/projects/", json={
        "name": "E2E Test Project",
        "description": "Test"
    }, headers=headers)
    project_id = proj_res.json().get("id")
    print(f"Project ID: {project_id}")

    print("4. Uploading source content...")
    source_res = requests.post(f"{BASE_URL}/orgs/{org_slug}/projects/{project_id}/sources/", json={
        "type": "ARTICLE",
        "title": "Test Source",
        "text_content": "This is a test document. Please process me Celery!",
        "project": project_id
    }, headers=headers)
    print("Source upload response:", source_res.status_code, source_res.text)
    
    source_id = source_res.json().get("id")
    if not source_id:
        print("Failed to get source ID. Exiting.")
        return

    print(f"Source ID: {source_id}")

    print("5. Waiting for Celery to process (15 seconds)...")
    for _ in range(15):
        time.sleep(1)
        res = requests.get(f"{BASE_URL}/orgs/{org_slug}/projects/{project_id}/sources/{source_id}/", headers=headers)
        status = res.json().get("status")
        print(f"Source Status: {status}")
        if status in ["COMPLETED", "FAILED"]:
            break

if __name__ == "__main__":
    run_test()
