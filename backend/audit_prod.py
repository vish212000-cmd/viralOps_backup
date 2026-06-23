import time
import requests
import uuid

API_URL = "https://viralops-web.onrender.com/api"

# Generate random user
username = f"auditor_{uuid.uuid4().hex[:8]}@example.com"
password = "TestPassword123!"

print(f"Creating user {username}...")
reg_res = requests.post(f"{API_URL}/auth/register/", json={
    "username": username,
    "email": username,
    "password": password,
    "password_confirm": password
})
print("Registration Status:", reg_res.status_code)
if reg_res.status_code not in [200, 201]:
    print("Registration Failed:", reg_res.text)
    exit(1)

# Log in
login_res = requests.post(f"{API_URL}/auth/login/", json={
    "username": username,
    "password": password
})
print("Login Status:", login_res.status_code)
if login_res.status_code != 200:
    print("Login Failed:", login_res.text)
    exit(1)

token = login_res.json().get("access")
headers = {"Authorization": f"Bearer {token}"}

# Create Workspace
print("Creating Workspace...")
ws_res = requests.post(f"{API_URL}/workspaces/", json={
    "name": "Audit Workspace"
}, headers=headers)
print("Workspace Status:", ws_res.status_code)
if ws_res.status_code not in [200, 201]:
    print("Workspace Failed:", ws_res.text)
    exit(1)

ws_id = ws_res.json().get("id")

# Create Project
print("Creating Project...")
start_time = time.time()
proj_res = requests.post(f"{API_URL}/projects/", json={
    "name": "Audit Test Video",
    "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "workspace": ws_id
}, headers=headers)
end_time = time.time()

elapsed = end_time - start_time
print("Project Create Status:", proj_res.status_code)
print(f"Time taken: {elapsed:.2f} seconds")

if proj_res.status_code in [200, 201]:
    data = proj_res.json()
    print("Project Data:", data)
    print("Initial Status:", data.get("status"))
    
    # Wait 5 seconds and poll status
    print("Waiting 5 seconds...")
    time.sleep(5)
    poll_res = requests.get(f"{API_URL}/projects/{data.get('id')}/", headers=headers)
    print("Poll Status:", poll_res.json().get("status"))
