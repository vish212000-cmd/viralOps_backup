import requests
import json
import time
import imaplib
import email
import re
import uuid

BASE_URL = "http://localhost:8000"
report = {}

email_addr = "kunl7sdwjbbp6rha@ethereal.email"
email_pass = "B4WeHDUNCKzMZwWPbu"
user_pass = "JourneyPassword123!"

def log_step(step, status, details=None):
    report[step] = {"status": status, "details": details}
    print(f"[{status}] {step}")
    if details:
        print(f"  -> {str(details)[:200]}")

# 1. SMTP Health Check
try:
    res = requests.get(f"{BASE_URL}/api/auth/smtp-health/")
    if res.status_code == 200:
        log_step("SMTP Health Check", "SUCCESS", res.json())
    else:
        log_step("SMTP Health Check", "FAILED", res.text)
except Exception as e:
    log_step("SMTP Health Check", "ERROR", str(e))

# Clear inbox
try:
    mail = imaplib.IMAP4_SSL('imap.ethereal.email', 993)
    mail.login(email_addr, email_pass)
    mail.select('inbox')
    typ, data = mail.search(None, 'ALL')
    for num in data[0].split():
        mail.store(num, '+FLAGS', '\\Deleted')
    mail.expunge()
    mail.logout()
    log_step("Clear Inbox", "SUCCESS", "Cleared old emails")
except Exception as e:
    log_step("Clear Inbox", "ERROR", str(e))

# 2. Signup
try:
    res = requests.post(f"{BASE_URL}/api/auth/register/", json={
        "username": email_addr,
        "email": email_addr,
        "password": user_pass,
        "first_name": "Test",
        "last_name": "User"
    })
    if res.status_code == 201:
        log_step("Signup", "SUCCESS")
    elif res.status_code == 400 and "already exists" in res.text:
        log_step("Signup", "SUCCESS", "User already exists (continuing test)")
        # Resend verification email
        resend = requests.post(f"{BASE_URL}/api/auth/resend-verification/", json={"email": email_addr})
        if resend.status_code in [200, 201]:
            log_step("Resend Email", "SUCCESS", "Requested new verification email")
        else:
            log_step("Resend Email", "FAILED", resend.text)
    else:
        log_step("Signup", "FAILED", res.text)
except Exception as e:
    log_step("Signup", "ERROR", str(e))

# 3. Read Inbox to extract Verification Link
verification_link = None
log_step("Reading Inbox", "INFO", "Waiting for email to arrive...")
time.sleep(5) # wait for delivery

try:
    mail = imaplib.IMAP4_SSL('imap.ethereal.email', 993)
    mail.login(email_addr, email_pass)
    mail.select('inbox')
    
    # Search for all emails with retries
    for _ in range(6):
        status, data = mail.search(None, 'ALL')
        mail_ids = data[0].split()
        if mail_ids:
            break
        time.sleep(5)
    
    if mail_ids:
        # Get the latest email
        latest_email_id = mail_ids[-1]
        status, data = mail.fetch(latest_email_id, '(RFC822)')
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)
        
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/html" or part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = msg.get_payload(decode=True).decode()
            
        # Regex to find the verification link
        # Expected: https://viral-ops-backup-aexx.vercel.app/verify-email?token=...
        match = re.search(r'https?://[^\s"\'<>]+/verify-email\?token=[^\s"\'<>]+', body)
        if match:
            verification_link = match.group(0)
            if 'localhost' in verification_link:
                log_step("Read Inbox", "FAILED", f"Hardcoded localhost found in link: {verification_link}")
                exit(1)
            token = verification_link.split('token=')[1]
            log_step("Read Inbox", "SUCCESS", f"Extracted token: {token}")
        else:
            log_step("Read Inbox", "FAILED", "Could not find verification link in email body")
    else:
        log_step("Read Inbox", "FAILED", "No emails found in inbox")
    mail.logout()
except Exception as e:
    log_step("Read Inbox", "ERROR", str(e))

# 4. Verify Email
if verification_link:
    token = verification_link.split('token=')[1]
    try:
        # Check backend verify endpoint
        res = requests.post(f"{BASE_URL}/api/auth/verify-email/", json={
            "token": token
        })
        if res.status_code == 200:
            log_step("Verify Email", "SUCCESS", "Email successfully verified")
        elif res.status_code == 400 and "already been verified" in res.text:
            log_step("Verify Email", "SUCCESS", "Email already verified")
        else:
            log_step("Verify Email", "FAILED", res.text)
    except Exception as e:
        log_step("Verify Email", "ERROR", str(e))

# 5. Login
token = None
try:
    res = requests.post(f"{BASE_URL}/api/auth/login/", json={
        "username": email_addr,
        "password": user_pass
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
    
    # Get Org Slug
    org_slug = "default"
    try:
        res = requests.get(f"{BASE_URL}/api/workspaces/", headers=headers)
        if res.status_code == 200:
            if len(res.json()) > 0:
                org_slug = res.json()[0].get("slug", "default")
                log_step("Fetch Org", "SUCCESS", f"Found existing org: {org_slug}")
            else:
                # Create the org
                create_res = requests.post(f"{BASE_URL}/api/workspaces/", json={"name": "My Workspace"}, headers=headers)
                if create_res.status_code == 201:
                    org_slug = create_res.json().get("slug", "default")
                    log_step("Fetch Org", "SUCCESS", f"Created org: {org_slug}")
                else:
                    log_step("Fetch Org", "FAILED", f"Failed to create org: {create_res.text}")
        else:
            log_step("Fetch Org", "FAILED", res.text)
    except Exception as e:
        log_step("Fetch Org", "ERROR", str(e))

    # Create Project
    project_id = None
    try:
        res = requests.post(f"{BASE_URL}/api/orgs/{org_slug}/projects/", json={
            "name": "Ethereal Test Project",
            "description": "Testing the full flow with real SMTP"
        }, headers=headers)
        if res.status_code == 201:
            project_id = res.json().get("id")
            log_step("Create Project", "SUCCESS", f"Project ID: {project_id}")
        else:
            log_step("Create Project", "FAILED", res.text)
    except Exception as e:
        log_step("Create Project", "ERROR", str(e))

with open('C:/Users/TCCSPL/.gemini/antigravity/brain/afc95b85-e151-49f3-acd4-9fff6b88a2ad/smtp_results.json', 'w') as f:
    json.dump(report, f, indent=2)

if all(step.get("status") == "SUCCESS" or step.get("status") == "INFO" for step in report.values()):
    print("\n[PASS] WORKFLOW COMPLETED SUCCESSFULLY")
else:
    print("\n[FAIL] WORKFLOW FAILED")
