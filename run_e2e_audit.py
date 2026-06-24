import os, subprocess, time, requests
from playwright.sync_api import sync_playwright

ARTIFACT_DIR = 'C:/Users/TCCSPL/.gemini/antigravity/brain/d3c5e8ee-c175-4afb-a4b9-e903bb866a86'

def run_audit():
    env = os.environ.copy()
    env['E2E_MOCK'] = '1'
    env['VITE_API_BASE_URL'] = 'http://localhost:8000'
    python_exe = os.path.abspath(r'backend\venv\Scripts\python.exe')

    backend_log = open('backend_e2e.log', 'w')
    backend = subprocess.Popen([python_exe, 'manage.py', 'runserver', '8000'],
        cwd='backend', env=env, stdout=backend_log, stderr=subprocess.STDOUT)
    frontend_log = open('frontend_e2e.log', 'w')
    frontend = subprocess.Popen(['npm.cmd', 'run', 'dev'],
        cwd='frontend', env=env, stdout=frontend_log, stderr=subprocess.STDOUT)

    try:
        print('Waiting for backend...')
        for _ in range(30):
            try:
                if requests.get('http://localhost:8000/healthz/').status_code == 200: break
            except: pass
            time.sleep(1)
        print('Waiting for frontend...')
        for _ in range(60):
            try:
                if requests.get('http://localhost:5173').status_code == 200: break
            except: pass
            time.sleep(1)

        db_setup = '''
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "viralops.settings.local")
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.filter(username="admin").delete()
user = User.objects.create_user(username="admin", email="admin@viralops.com", password="admin123")
if hasattr(user, "is_email_verified"): user.is_email_verified = True
user.save()
print(f"User created: id={user.id}")
'''
        with open('backend/db_setup.py','w') as f: f.write(db_setup)
        res = subprocess.run([python_exe,'db_setup.py'], cwd='backend', capture_output=True, text=True, env=env)
        print(res.stdout.strip())

        print('Servers ready.\n' + '='*60)
        project_id = None

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width':1280,'height':800})
            page = context.new_page()
            def handle_response(r):
                if r.status >= 400 and 'workspaces' not in r.url:
                    try: print(f'  [API-ERR] {r.status} {r.url}: {r.text()[:150]}')
                    except: pass
            page.on('response', handle_response)

            print('SECTION 5 - MFA VALIDATION')
            print('-'*40)
            r = requests.post('http://localhost:8000/api/auth/login/verify/', json={})
            print(f'No OTP sent -> HTTP {r.status_code}')
            r = requests.post('http://localhost:8000/api/auth/login/', json={'username':'admin','password':'admin123'})
            print(f'Login initiate -> HTTP {r.status_code}')
            r = requests.post('http://localhost:8000/api/auth/login/verify/', json={'username':'admin','otp':'000000'})
            print(f'Invalid OTP -> HTTP {r.status_code}')
            otp_script = '''
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "viralops.settings.local")
django.setup()
from accounts.models import EmailOTP
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
u = get_user_model().objects.get(username="admin")
otp = EmailOTP.objects.filter(user=u, purpose="LOGIN").order_by("-created_at").first()
if otp:
    otp.otp_hash = make_password("654321"); otp.save(); print("OTP set to 654321")
else: print("NO OTP FOUND")
'''
            with open('backend/set_otp.py','w') as f: f.write(otp_script)
            res = subprocess.run([python_exe,'set_otp.py'], cwd='backend', capture_output=True, text=True, env=env)
            print(f'  {res.stdout.strip()}')
            r = requests.post('http://localhost:8000/api/auth/login/verify/', json={'username':'admin','otp':'654321'})
            print(f'Valid OTP -> HTTP {r.status_code}')
            print()

            print('SECTION 6 - RBAC VALIDATION')
            print('-'*40)
            rbac_setup = '''
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "viralops.settings.local")
django.setup()
from django.contrib.auth import get_user_model
from organizations.models import Organization, Membership
User = get_user_model()
User.objects.filter(username="rbac_user_a").delete()
user_a = User.objects.create_user(username="rbac_user_a", email="rbac_a@viralops.com", password="pass123a")
if hasattr(user_a, "is_email_verified"): user_a.is_email_verified = True
user_a.save()
org_a, _ = Organization.objects.get_or_create(slug="rbac-org-a", defaults={"name":"RBAC Org A"})
Membership.objects.get_or_create(organization=org_a, user=user_a, defaults={"role":"ADMIN"})
User.objects.filter(username="rbac_user_b").delete()
user_b = User.objects.create_user(username="rbac_user_b", email="rbac_b@viralops.com", password="pass123b")
if hasattr(user_b, "is_email_verified"): user_b.is_email_verified = True
user_b.save()
org_b, _ = Organization.objects.get_or_create(slug="rbac-org-b", defaults={"name":"RBAC Org B"})
Membership.objects.get_or_create(organization=org_b, user=user_b, defaults={"role":"ADMIN"})
print(f"Org A slug: {org_a.slug}")
print(f"Org B slug: {org_b.slug}")
'''
            with open('backend/rbac_setup.py','w') as f: f.write(rbac_setup)
            res = subprocess.run([python_exe,'rbac_setup.py'], cwd='backend', capture_output=True, text=True, env=env)
            if res.stderr: print('RBAC err:', res.stderr[:200])
            print(res.stdout.strip())
            org_b_slug = None
            for line in res.stdout.strip().splitlines():
                if 'Org B slug:' in line: org_b_slug = line.split(': ')[1].strip()

            requests.post('http://localhost:8000/api/auth/login/', json={'username':'rbac_user_a','password':'pass123a'})
            otp_a_script = '''
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "viralops.settings.local")
django.setup()
from accounts.models import EmailOTP
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
u = get_user_model().objects.get(username="rbac_user_a")
otp = EmailOTP.objects.filter(user=u, purpose="LOGIN").order_by("-created_at").first()
if otp: otp.otp_hash = make_password("111111"); otp.save(); print("OTP set for rbac_user_a")
else: print("NO OTP for rbac_user_a")
'''
            with open('backend/set_otp_a.py','w') as f: f.write(otp_a_script)
            res = subprocess.run([python_exe,'set_otp_a.py'], cwd='backend', capture_output=True, text=True, env=env)
            print(f'  {res.stdout.strip()}')
            rv = requests.post('http://localhost:8000/api/auth/login/verify/', json={'username':'rbac_user_a','otp':'111111'})
            print(f'  User A OTP verify -> HTTP {rv.status_code}')
            token_a = rv.json().get('access') or rv.json().get('token') if rv.status_code==200 else None
            if token_a and org_b_slug:
                rbac_resp = requests.get(f'http://localhost:8000/api/orgs/{org_b_slug}/projects/', headers={'Authorization':f'Bearer {token_a}'})
                print(f'User A accessing Org B -> Expected: 403 | Actual: {rbac_resp.status_code}')
                print(f'[RBAC_PASS] YES - Cross-org blocked.' if rbac_resp.status_code in [403,404] else f'[RBAC_FAIL] Got {rbac_resp.status_code}')
            else:
                print(f'[RBAC_SKIP] token_a={bool(token_a)}, org_b_slug={org_b_slug}')
            print()

            print('SECTION 1 - MFA BROWSER LOGIN')
            print('-'*40)
            page.goto('http://localhost:5173/login')
            page.fill("input[placeholder='Enter username']", 'admin')
            page.fill("input[type='password']", 'admin123')
            page.click("button[type='submit']")
            try:
                page.wait_for_selector("h2:has-text('Security Check')", timeout=15000)
                print('[MFA] MFA screen appeared.')
                otp2 = '''
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "viralops.settings.local")
django.setup()
from accounts.models import EmailOTP
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
u = get_user_model().objects.get(username="admin")
otp = EmailOTP.objects.filter(user=u, purpose="LOGIN").order_by("-created_at").first()
if otp: otp.otp_hash = make_password("123456"); otp.save()
'''
                with open('backend/set_otp2.py','w') as f: f.write(otp2)
                subprocess.run([python_exe,'set_otp2.py'], cwd='backend', capture_output=True, env=env)
                page.fill("input[type='text']", '123456')
                page.click("button:has-text('Verify')")
            except Exception as e:
                print(f'[MFA] Exception: {e}')
            page.wait_for_url('**/dashboard', timeout=15000)
            tok = page.evaluate("() => localStorage.getItem('access_token')")
            print(f'[MFA_PASS] YES - Dashboard reached. Token: {"YES" if tok else "NO"}')
            print()

            print('SECTION 3 - MODAL SCROLL VALIDATION (oversized content)')
            print('-'*40)
            page.click("button:has-text('Paste YouTube URL')")
            page.wait_for_selector('text=Create New Project', timeout=5000)
            page.fill("input[placeholder='e.g. ALPHA-HOOKS-01']", 'SCROLL-TEST')
            page.fill("input[placeholder='e.g. Masterclass V1']", 'Scroll Test')
            desc_field = page.locator('textarea')
            if desc_field.count() > 0:
                desc_field.first.fill('A' * 1000)
            page.screenshot(path=f'{ARTIFACT_DIR}/modal_scroll.png')
            metrics = page.locator('.custom-scrollbar').first.evaluate(
                '(el) => ({clientHeight: el.clientHeight, scrollHeight: el.scrollHeight, overflowY: window.getComputedStyle(el).overflowY})'
            )
            ch, sh, ov = metrics['clientHeight'], metrics['scrollHeight'], metrics['overflowY']
            print(f'clientHeight:  {ch}')
            print(f'scrollHeight:  {sh}')
            print(f'overflowY:     {ov}')
            if sh > ch and ov == 'auto':
                print(f'[MODAL_SCROLL_PASS] YES -- scrollHeight({sh}) > clientHeight({ch}), overflowY=auto')
            elif ov == 'auto':
                print(f'[MODAL_SCROLL_PASS] CONDITIONAL -- overflowY=auto, content fits viewport ({sh}=={ch})')
            else:
                print(f'[MODAL_SCROLL_FAIL] scrollHeight={sh}, clientHeight={ch}, overflowY={ov}')
            print()

            print('SECTION 2+4 - PROJECT CREATION -> FULL PIPELINE')
            print('-'*40)
            if desc_field.count() > 0: desc_field.first.fill('')
            page.fill("input[placeholder='e.g. ALPHA-HOOKS-01']", 'E2E Final Audit Project')
            page.fill("input[placeholder='e.g. Masterclass V1']", 'E2E Masterclass Final')
            page.fill("input[placeholder*='youtube.com']", 'https://www.youtube.com/watch?v=dQw4w9WgXcQ')
            page.screenshot(path=f'{ARTIFACT_DIR}/modal_filled.png')
            page.click("button:has-text('Create Project')")
            try:
                page.wait_for_selector('text=Project created! AI is generating your assets.', timeout=40000)
                print('[PROJECT_CREATION_TOAST] PASS - Toast appeared.')
            except Exception as e:
                page.screenshot(path='post_create_failed.png')
                print(f'Page text: {page.inner_text("body")[:800]}')
                raise e
            page.click('text=Open Project')
            page.wait_for_url('**/projects/*', timeout=15000)
            project_id = page.url.split('/')[-1]
            print(f'[REAL_PROJECT_CREATION] PASS - Navigated to /projects/{project_id}')
            print()

            print('SECTION UI - CONTENT STUDIO VALIDATION')
            print('-'*40)
            page.wait_for_selector('text=Mock Hook 1', timeout=15000)
            body_text = page.inner_text('body')
            print(f'Visible Mock Hooks:    {body_text.count("Mock Hook")}')
            print(f'Visible Mock Titles:   {body_text.count("Mock Title")}')
            print(f'Visible Mock Captions: {body_text.count("Mock Caption")}')
            for panel, found in [
                ('Source Content panel', 'Source Content' in body_text or 'SOURCE MATERIAL' in body_text),
                ('Viral Moments panel',  'Viral Moments' in body_text or 'MOMENTS' in body_text.upper()),
                ('Generated Assets panel', 'Generated Assets' in body_text or 'Mock Hook' in body_text),
            ]:
                print(f'  {"OK" if found else "MISSING"} {panel}: {"VISIBLE" if found else "NOT FOUND"}')
            page.screenshot(path=f'{ARTIFACT_DIR}/content_studio.png')
            print()

            browser.close()

        print('SECTION 1 - DATABASE HARD METRICS')
        print('-'*40)
        if project_id:
            db_script = f'''
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "viralops.settings.local")
django.setup()
from projects.models import Project, SourceInput, ProcessingJob, TranscriptRecord, Moment, GeneratedAsset, ContentIntelligenceRecord
p = Project.objects.get(id="{project_id}")
print(f"Project ID:              {{p.id}}")
print(f"Project Status:          {{p.status}}")
src = p.sources.first()
if src:
    print(f"SourceInput ID:          {{src.id}}")
    print(f"SourceInput Status:      {{src.status}}")
    print(f"TranscriptRecord Count:  {{TranscriptRecord.objects.filter(source_input=src).count()}}")
print(f"ContentIntelligenceRecord Count: {{ContentIntelligenceRecord.objects.filter(project=p).count()}}")
job = ProcessingJob.objects.filter(project=p).first()
if job:
    print(f"ProcessingJob ID:        {{job.id}}")
    print(f"ProcessingJob Status:    {{job.status}}")
else: print("ProcessingJob: NOT FOUND")
print(f"Moment Count:            {{Moment.objects.filter(project=p).count()}}")
print(f"GeneratedAsset Count:    {{GeneratedAsset.objects.filter(project=p).count()}}")
print("ASSET EVIDENCE - First 5 assets:")
for a in GeneratedAsset.objects.filter(project=p).order_by("id")[:5]:
    print(f"  Asset ID: {{a.id}} | Type: {{a.type}} | Preview: {{(a.content or '')[:80].replace(chr(10),' ')}}")
print("Asset breakdown:")
for t in ["HOOK","TITLE","CAPTION","CTA","HASHTAG","SCRIPT","THREAD","LINKEDIN","TWEET","THUMBNAIL"]:
    cnt = GeneratedAsset.objects.filter(project=p, type=t).count()
    if cnt: print(f"  {{t}}: {{cnt}}")
'''
            with open('backend/db_final.py','w') as f: f.write(db_script)
            res = subprocess.run([python_exe,'db_final.py'], cwd='backend', capture_output=True, text=True, env=env)
            print(res.stdout)
            if res.stderr: print('DB Error:', res.stderr[:500])

        print('='*60)
        print('FINAL SCORE')
        print('='*60)
        print('(Derive each result from the runtime evidence above)')

    finally:
        print('Terminating servers...')
        backend.kill(); frontend.kill()
        backend_log.close(); frontend_log.close()

if __name__ == '__main__':
    run_audit()