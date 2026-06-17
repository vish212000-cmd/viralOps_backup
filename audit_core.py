import requests
import json
import time
import imaplib
import email
import re
import uuid

BASE_URL = "https://viralops-web.onrender.com"
FRONTEND_URL = "https://viral-ops-backup-aexx.vercel.app"

# Ethereal credentials
EMAIL_ADDR = "kunl7sdwjbbp6rha@ethereal.email"
EMAIL_PASS = "B4WeHDUNCKzMZwWPbu"

USER_PASS = "ProductionAudit123!"
UUID_SUFFIX = uuid.uuid4().hex[:8]

report = {
    "auth": {},
    "workspaces": {},
    "projects": {},
    "ingestion": {},
    "ai_generation": {},
    "billing": {},
    "cleanup": {}
}

def log_step(category, step, status, details=None):
    report[category][step] = {"status": status, "details": details}
    print(f"[{status}] {step}")
    if details:
        print(f"  -> {str(details)[:200]}")

# 1. Clear Inbox
try:
    mail = imaplib.IMAP4_SSL('imap.ethereal.email', 993)
    mail.login(EMAIL_ADDR, EMAIL_PASS)
    mail.select('inbox')
    typ, data = mail.search(None, 'ALL')
    for num in data[0].split():
        mail.store(num, '+FLAGS', '\\Deleted')
    mail.expunge()
    mail.logout()
    log_step("auth", "Clear Inbox", "PASS")
except Exception as e:
    log_step("auth", "Clear Inbox", "WARN", str(e))

# 2. Signup
test_email = "k4pegmelcz7nkyty@ethereal.email"
try:
    res = requests.post(f"{BASE_URL}/api/auth/register/", json={
        "username": test_email,
        "email": test_email,
        "password": USER_PASS,
        "first_name": "Audit",
        "last_name": "User"
    })
    if res.status_code == 201:
        log_step("auth", "Signup", "PASS")
    elif res.status_code == 400 and "already exists" in res.text:
        log_step("auth", "Signup", "PASS", "User already exists")
        resend = requests.post(f"{BASE_URL}/api/auth/resend-verification/", json={"email": test_email})
        if resend.status_code in [200, 201]:
             log_step("auth", "Resend Verification", "PASS")
        else:
             log_step("auth", "Resend Verification", "FAIL", resend.text)
    else:
        log_step("auth", "Signup", "FAIL", res.text)
except Exception as e:
    log_step("auth", "Signup", "FAIL", str(e))

# 3. Read Verification Link
verification_link = None
log_step("auth", "Read Verification Email", "INFO", "Waiting for email...")
time.sleep(8)
try:
    mail = imaplib.IMAP4_SSL('imap.ethereal.email', 993)
    mail.login(EMAIL_ADDR, EMAIL_PASS)
    mail.select('inbox')
    
    for _ in range(6):
        status, data = mail.search(None, 'ALL')
        mail_ids = data[0].split()
        if mail_ids:
            break
        time.sleep(5)
    
    if mail_ids:
        latest_email_id = mail_ids[-1]
        status, data = mail.fetch(latest_email_id, '(RFC822)')
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)
        
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() in ["text/html", "text/plain"]:
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = msg.get_payload(decode=True).decode()
            
        match = re.search(r'https?://[^\s"\'<>]+/verify-email\?token=[^\s"\'<>]+', body)
        if match:
            verification_link = match.group(0)
            if 'localhost' in verification_link:
                log_step("auth", "Read Verification Email", "FAIL", f"Hardcoded localhost: {verification_link}")
            else:
                token = verification_link.split('token=')[1]
                log_step("auth", "Read Verification Email", "PASS", f"Token found")
        else:
            log_step("auth", "Read Verification Email", "FAIL", "No verification link found")
    else:
        log_step("auth", "Read Verification Email", "FAIL", "No emails arrived")
    mail.logout()
except Exception as e:
    log_step("auth", "Read Verification Email", "FAIL", str(e))

# 4. Verify Email
if verification_link:
    token = verification_link.split('token=')[1]
    try:
        res = requests.post(f"{BASE_URL}/api/auth/verify-email/", json={"token": token})
        if res.status_code == 200:
            log_step("auth", "Verify Email", "PASS")
        else:
            log_step("auth", "Verify Email", "FAIL", res.text)
    except Exception as e:
        log_step("auth", "Verify Email", "FAIL", str(e))

# 5. Login
auth_token = None
try:
    res = requests.post(f"{BASE_URL}/api/auth/login/", json={
        "username": test_email,
        "password": USER_PASS
    })
    if res.status_code == 200:
        auth_token = res.json().get("access")
        log_step("auth", "Login", "PASS")
    else:
        log_step("auth", "Login", "FAIL", res.text)
except Exception as e:
    log_step("auth", "Login", "FAIL", str(e))

org_slug = None
project_id = None
if auth_token:
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # 6. Create Workspace
    try:
        res = requests.post(f"{BASE_URL}/api/workspaces/", json={"name": f"Audit WS {UUID_SUFFIX}"}, headers=headers)
        if res.status_code == 201:
            org_slug = res.json().get("slug")
            log_step("workspaces", "Create Workspace", "PASS", f"Slug: {org_slug}")
        else:
            log_step("workspaces", "Create Workspace", "FAIL", res.text)
    except Exception as e:
        log_step("workspaces", "Create Workspace", "FAIL", str(e))
        
    # 7. Create Project
    if org_slug:
        try:
            res = requests.post(f"{BASE_URL}/api/orgs/{org_slug}/projects/", json={
                "name": "Audit Project",
                "description": "Production validation project"
            }, headers=headers)
            if res.status_code == 201:
                project_id = res.json().get("id")
                log_step("projects", "Create Project", "PASS", f"ID: {project_id}")
            else:
                log_step("projects", "Create Project", "FAIL", res.text)
        except Exception as e:
            log_step("projects", "Create Project", "FAIL", str(e))

    # 8. Source Ingestion
    source_id = None
    if project_id:
        try:
            res = requests.post(f"{BASE_URL}/api/orgs/{org_slug}/projects/{project_id}/sources/", json={
                "project": project_id,
                "type": "text",
                "title": "Audit Source",
                "text_content": "This is a short audit text. It needs to be processed to generate a transcript."
            }, headers=headers)
            if res.status_code == 201:
                source_id = res.json().get("id")
                log_step("ingestion", "Upload Source", "PASS", f"Source ID: {source_id}")
            else:
                log_step("ingestion", "Upload Source", "FAIL", res.text)
        except Exception as e:
            log_step("ingestion", "Upload Source", "FAIL", str(e))
            
    # 9. Trigger Processing / Celery
    if source_id:
        try:
            # Process source
            res = requests.post(f"{BASE_URL}/api/orgs/{org_slug}/projects/{project_id}/sources/{source_id}/process/", headers=headers)
            if res.status_code in [200, 202]:
                log_step("ingestion", "Trigger Process", "PASS", res.json())
                
                # Wait for celery
                for _ in range(6):
                    time.sleep(5)
                    s_res = requests.get(f"{BASE_URL}/api/orgs/{org_slug}/projects/{project_id}/sources/{source_id}/", headers=headers)
                    if s_res.json().get("status") in ["processed", "completed"]:
                        log_step("ingestion", "Celery Task Consumed", "PASS", "Status is processed")
                        break
                    elif s_res.json().get("status") == "failed":
                        log_step("ingestion", "Celery Task Consumed", "FAIL", s_res.json().get("error_message"))
                        break
                else:
                    log_step("ingestion", "Celery Task Consumed", "FAIL", "Timeout waiting for processing")
            else:
                log_step("ingestion", "Trigger Process", "FAIL", res.text)
        except Exception as e:
            log_step("ingestion", "Trigger Process", "FAIL", str(e))

    # 10. AI Generation (Generate Assets from project moments)
    if project_id:
        try:
            res = requests.post(f"{BASE_URL}/api/orgs/{org_slug}/projects/{project_id}/generate/", json={}, headers=headers)
            if res.status_code in [200, 201, 202]:
                log_step("ai_generation", "Trigger Gemini", "PASS", "Accepted")
            else:
                log_step("ai_generation", "Trigger Gemini", "FAIL", res.text)
        except Exception as e:
            log_step("ai_generation", "Trigger Gemini", "FAIL", str(e))

    # 11. Billing Verification
    try:
        res = requests.get(f"{BASE_URL}/api/billing/plans/", headers=headers)
        if res.status_code == 200:
            log_step("billing", "Fetch Plans", "PASS")
        else:
            log_step("billing", "Fetch Plans", "FAIL", res.text)
    except Exception as e:
        log_step("billing", "Fetch Plans", "FAIL", str(e))

    # 12. Cleanup (Workspaces)
    if org_slug:
        try:
            res = requests.delete(f"{BASE_URL}/api/workspaces/{org_slug}/", headers=headers)
            if res.status_code == 204:
                log_step("cleanup", "Delete Workspace", "PASS")
            else:
                log_step("cleanup", "Delete Workspace", "FAIL", res.text)
        except Exception as e:
            log_step("cleanup", "Delete Workspace", "FAIL", str(e))

with open("core_audit.json", "w") as f:
    json.dump(report, f, indent=2)

print("\nSaved core_audit.json")
