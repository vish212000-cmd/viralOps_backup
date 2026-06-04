import os
import sys
import traceback
import requests

def get_or_create_smoke_test_credentials():
    """Fetch or create a test user and org inside Django context"""
    try:
        from django.contrib.auth import get_user_model
        from organizations.models import Organization, Membership
        
        User = get_user_model()
        email = os.getenv('SMOKE_TEST_EMAIL', 'smoketest@viralops.com')
        username = os.getenv('SMOKE_TEST_USERNAME', 'smoketest')
        password = os.getenv('SMOKE_TEST_PASSWORD', 'SmokeTestPass123!')
        org_slug = os.getenv('SMOKE_TEST_ORG_SLUG', 'smoke-test-org')

        user, created = User.objects.get_or_create(email=email, defaults={'username': username})
        if created or not user.check_password(password):
            user.set_password(password)
            user.is_active = True
            user.save()

        org, _ = Organization.objects.get_or_create(slug=org_slug, defaults={'name': 'Smoke Test Org'})
        Membership.objects.get_or_create(user=user, organization=org, defaults={'role': 'ADMIN'})

        return email, password, org_slug
    except Exception as e:
        print(f"Django DB context missing or failed to initialize credentials: {str(e)}")
        # Fallback to env vars if we are running completely standalone outside Django
        return (
            os.getenv('SMOKE_TEST_EMAIL', 'smoketest@viralops.com'),
            os.getenv('SMOKE_TEST_PASSWORD', 'SmokeTestPass123!'),
            os.getenv('SMOKE_TEST_ORG_SLUG', 'smoke-test-org')
        )

def run_smoke_tests(base_url: str):
    """End-to-end post-deployment verification tests"""
    print("Preparing smoke test verification account...")
    email, password, org_slug = get_or_create_smoke_test_credentials()

    tests_run = 0
    tests_passed = 0
    token = None

    # Helper function to run a test and print output
    def assert_test(name, method, url, status=200, headers=None, json_data=None, search_body=None):
        nonlocal tests_run, tests_passed
        tests_run += 1
        print(f"Running Test {tests_run}: {name} ({method} {url.replace(base_url, '')})")
        try:
            if method == 'GET':
                r = requests.get(url, headers=headers)
            elif method == 'POST':
                r = requests.post(url, headers=headers, json=json_data)
            else:
                print(f"  [FAIL] Unknown method {method}")
                return False

            if r.status_code != status:
                print(f"  [FAIL] Expected status {status}, got {r.status_code}")
                print(f"  Response Body: {r.text[:200]}")
                return False

            if search_body and search_body not in r.text:
                print(f"  [FAIL] Could not find '{search_body}' in response body")
                print(f"  Response Body: {r.text[:200]}")
                return False

            print(f"  [PASS] Status {r.status_code} verified.")
            tests_passed += 1
            return r
        except Exception as e:
            print(f"  [FAIL] Connection/Request failure: {str(e)}")
            traceback.print_exc()
            return False

    # 1. Unauthenticated Health Check (Liveness)
    assert_test("Health Check Liveness", "GET", f"{base_url}/healthz/", 200, search_body="UP")

    # 2. Unauthenticated Readiness Check
    assert_test("Readiness Check", "GET", f"{base_url}/ready/", 200, search_body="READY")

    # 3. Unauthenticated Prometheus Metrics Format
    assert_test("Prometheus Metrics Format", "GET", f"{base_url}/prometheus/metrics", 200, search_body="viralops_api_requests_total")

    # 4. Authenticate & Obtain Tokens
    login_resp = assert_test(
        "User Login Authentication",
        "POST",
        f"{base_url}/api/auth/login/",
        200,
        json_data={"email": email, "password": password},
        search_body="access"
    )

    if login_resp:
        try:
            token = login_resp.json().get('access')
        except Exception:
            pass

    if not token:
        print("[CRITICAL] Token retrieval failed. Authenticated smoke tests skipped.")
        return False

    auth_headers = {
        'Authorization': f'Bearer {token}',
        'X-Org-Slug': org_slug
    }

    # 5. Fetch Projects List (Authenticated)
    assert_test(
        "Fetch Workspace Projects",
        "GET",
        f"{base_url}/api/orgs/{org_slug}/projects/",
        200,
        headers=auth_headers
    )

    # 6. Retrieve Billing Plans
    assert_test(
        "Fetch Billing Plans",
        "GET",
        f"{base_url}/api/billing/plans/",
        200,
        headers=auth_headers
    )

    # 7. Access Workspace Analytics Summary
    assert_test(
        "Fetch Workspace Analytics Summary",
        "GET",
        f"{base_url}/api/analytics/orgs/{org_slug}/workspace/summary/",
        200,
        headers=auth_headers
    )

    print(f"\nSmoke test execution summary: {tests_passed}/{tests_run} tests passed.")
    return tests_passed == tests_run

if __name__ == '__main__':
    url = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8000'
    success = run_smoke_tests(url)
    sys.exit(0 if success else 1)
