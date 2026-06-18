import os
import django
import json
import traceback

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "viralops.settings")
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from projects.models import Organization, Project, SourceInput, ProcessingJob
from rest_framework_simplejwt.tokens import RefreshToken
from projects.tasks import process_source_input
from django.test import override_settings

User = get_user_model()
c = Client(SERVER_NAME='localhost')

print("\n===========================================")
print(" PRODUCTION VERIFICATION AUDIT - VIRALOPS ")
print("===========================================\n")

from organizations.models import Organization, Membership

# Setup User and Org
user, _ = User.objects.get_or_create(email="audit@example.com", defaults={"first_name": "Audit", "is_active": True})
user.set_password("auditpassword")
user.save()

org, _ = Organization.objects.get_or_create(name="Audit Org", slug="audit-org")
if not Membership.objects.filter(user=user, organization=org).exists():
    Membership.objects.create(user=user, organization=org, role='ADMIN')

# Delete old projects to avoid hitting quota
Project.objects.filter(organization=org).delete()

refresh = RefreshToken.for_user(user)
token = str(refresh.access_token)
headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

# --- 1. Successful YouTube Ingestion ---
print("\n--- TEST 1: SUCCESSFUL PATH ---")

res1_proj = c.post(f"/api/orgs/{org.slug}/projects/", data=json.dumps({"name": "Audit Project Success"}), content_type="application/json", **headers)
print("Project Creation Status Code:", res1_proj.status_code)
if res1_proj.status_code >= 400:
    print("Error:", res1_proj.content.decode())
    
p_id = res1_proj.json()["id"]

source_payload = {
    "type": "YOUTUBE",
    "source_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
res1_src = c.post(f"/api/orgs/{org.slug}/projects/{p_id}/sources/", data=json.dumps(source_payload), content_type="application/json", **headers)
print("Source Creation Status Code:", res1_src.status_code)
if res1_src.status_code >= 400:
    print("Source Error:", res1_src.content.decode())

project = Project.objects.get(id=p_id)
source = project.sources.first()
job = project.jobs.first()

print("Initial Project Status:", project.status)
print("Initial SourceInput Status:", getattr(source, "status", "MISSING"))
print("Initial ProcessingJob Status:", getattr(job, "status", "MISSING"))
print("\nStarting Processing (Synchronous Execution)...")
try:
    process_source_input(source.id)
except Exception as e:
    print(f"Exception during processing: {e}")

project.refresh_from_db()
source.refresh_from_db()

print("\nVerification Evidence (Success Path):")
print(f"Project Status: {project.status}")
print(f"SourceInput Status: {source.status}")
print(f"SourceInput Transcript Length: {source.transcript_length}")
print(f"SourceInput Transcript Method: {source.transcript_retrieval_method}")

job = ProcessingJob.objects.filter(source_input=source).order_by('-created_at').first()
if job:
    print(f"ProcessingJob Status: {job.status}")
else:
    print("No ProcessingJob found.")

print(f"Project Assets Generated: {project.assets.count()}")

# --- 2. Failed YouTube Ingestion ---
print("\n--- TEST 2: FAILURE PATH ---")

res2_proj = c.post(f"/api/orgs/{org.slug}/projects/", data=json.dumps({"name": "Audit Project Fail"}), content_type="application/json", **headers)
print("Fail Project Creation Status Code:", res2_proj.status_code)
if res2_proj.status_code >= 400:
    print("Error:", res2_proj.content.decode())
p_id2 = res2_proj.json()["id"]

source_fail_payload = {
    "type": "YOUTUBE",
    "source_url": "https://www.youtube.com/watch?v=invalid_id_123"
}
res2_src = c.post(f"/api/orgs/{org.slug}/projects/{p_id2}/sources/", data=json.dumps(source_fail_payload), content_type="application/json", **headers)
print("Fail Source Creation Status:", res2_src.status_code)

project2 = Project.objects.get(id=p_id2)
source2 = project2.sources.first()
job2 = project2.jobs.first()

print("\nStarting Processing (Synchronous Execution) for invalid video...")
try:
    process_source_input(source2.id)
except Exception as e:
    print(f"Exception during processing: {e}")

project2.refresh_from_db()
source2.refresh_from_db()
job2 = ProcessingJob.objects.filter(source_input=source2).order_by('-created_at').first()

print("\nVerification Evidence (Failure Path):")
print(f"Project Status: {project2.status}")
print(f"SourceInput Status: {source2.status}")
if job2:
    print(f"ProcessingJob Status: {job2.status}")
    print(f"ProcessingJob Error Type: {job2.error_type}")
    print(f"ProcessingJob Error Message: {job2.error_message}")
    print(f"ProcessingJob Failing Step: {job2.failing_step}")

# Check API response to ensure error is propagated
res2_get = c.get(f"/api/orgs/{org.slug}/projects/{p_id2}/", **headers)
print("API Exposes Error Message:", res2_get.json().get("error_message"))

# --- 3. Retry Endpoint ---
print("\n--- TEST 3: RETRY ENDPOINT ---")
print("Issuing POST /api/orgs/<slug>/projects/<id>/retry/ to the failed project...")
res3 = c.post(f"/api/orgs/{org.slug}/projects/{p_id2}/retry/", **headers)
print("Retry Status Code:", res3.status_code)
print("Retry Response:", res3.json() if res3.content else "")

project2.refresh_from_db()
source2.refresh_from_db()

print("\nVerification Evidence (Retry Path):")
print(f"Project Status: {project2.status}")
print(f"SourceInput Status: {source2.status}")

print("\n===========================================")
print(" AUDIT COMPLETE")
print("===========================================\n")
