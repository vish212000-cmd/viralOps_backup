import requests
import json
import time

BACKEND_URL = "https://viralops-web.onrender.com"
FRONTEND_URL = "https://viral-ops-backup-aexx.vercel.app"

report = {
    "infrastructure": {},
    "security": {},
    "performance": {}
}

def check(category, test_name, status, details=None):
    report[category][test_name] = {"status": status, "details": details}
    print(f"[{status}] {test_name}: {str(details)[:200] if details else ''}")

print("=== BLOCK 1: INFRASTRUCTURE & HEALTH ===")

# 1. Backend Health
try:
    start_time = time.time()
    res = requests.get(f"{BACKEND_URL}/healthz/")
    elapsed = round(time.time() - start_time, 2)
    if res.status_code == 200:
        check("infrastructure", "Backend /healthz/", "PASS", res.json())
        check("performance", "Backend /healthz/ Response Time", "PASS" if elapsed < 1.0 else "WARN", f"{elapsed}s")
    else:
        check("infrastructure", "Backend /healthz/", "FAIL", f"Status {res.status_code}: {res.text}")
except Exception as e:
    check("infrastructure", "Backend /healthz/", "FAIL", str(e))

# 2. Frontend Health
try:
    start_time = time.time()
    res = requests.get(f"{FRONTEND_URL}")
    elapsed = round(time.time() - start_time, 2)
    if res.status_code == 200:
        check("infrastructure", "Frontend URL", "PASS", f"Loaded HTML ({len(res.text)} bytes)")
        check("performance", "Frontend Root Response Time", "PASS" if elapsed < 1.0 else "WARN", f"{elapsed}s")
    else:
        check("infrastructure", "Frontend URL", "FAIL", f"Status {res.status_code}")
except Exception as e:
    check("infrastructure", "Frontend URL", "FAIL", str(e))

# 3. SMTP / Redis / Celery via API endpoints
try:
    res = requests.get(f"{BACKEND_URL}/api/auth/smtp-health/")
    if res.status_code == 200:
        check("infrastructure", "SMTP Health", "PASS", res.json())
    else:
        check("infrastructure", "SMTP Health", "FAIL", res.text)
except Exception as e:
    check("infrastructure", "SMTP Health", "FAIL", str(e))

# 4. Security Headers (CORS)
try:
    res = requests.options(f"{BACKEND_URL}/api/auth/login/", headers={"Origin": FRONTEND_URL})
    if res.status_code in [200, 204]:
        acao = res.headers.get("Access-Control-Allow-Origin")
        if acao == FRONTEND_URL:
            check("security", "CORS Allowed Origin", "PASS", acao)
        elif acao == "*":
            check("security", "CORS Allowed Origin", "FAIL", "CORS is excessively permissive (*)")
        else:
            check("security", "CORS Allowed Origin", "FAIL", f"Expected {FRONTEND_URL}, got {acao}")
    else:
        check("security", "CORS OPTIONS request", "FAIL", res.status_code)
except Exception as e:
    check("security", "CORS", "FAIL", str(e))

# Dump report
with open("infrastructure_audit.json", "w") as f:
    json.dump(report, f, indent=2)

print("\nSaved report to infrastructure_audit.json")
