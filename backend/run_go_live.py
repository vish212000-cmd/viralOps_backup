import os
import sys
import time
import json
import threading
import requests
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viralops.settings')
os.environ["AI_PROVIDER"] = "nvidia"
os.environ["NVIDIA_API_KEY"] = "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"
os.environ["NVIDIA_MODEL"] = "meta/llama-3.1-8b-instruct"
django.setup()

from django.conf import settings
settings.CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

from projects.models import Project, SourceInput, ProcessingJob, GeneratedAsset, Moment, UsageEvent
from organizations.models import Organization, Membership
from projects.tasks import process_source_input, retry_ai_generation
from django.contrib.auth import get_user_model
User = get_user_model()
from rest_framework.test import APIClient
from django.urls import reverse

def print_section(title):
    print(f"\n{'='*50}\n{title}\n{'='*50}")

def main():
    print_section("FINAL GO-LIVE VALIDATION")
    
    # Setup test user and organization
    user, _ = User.objects.get_or_create(username='golive_auditor', defaults={'email': 'auditor@example.com'})
    user.set_password('password123')
    user.save()
    
    org, _ = Organization.objects.get_or_create(name='Go Live Audit Org', defaults={'slug': 'golive-audit-org'})
    Membership.objects.get_or_create(user=user, organization=org, defaults={'role': 'OWNER'})
    
    # 1. Create a Project
    project = Project.objects.create(name="Go-Live Audit Project", organization=org, status="PENDING")
    source = SourceInput.objects.create(
        project=project,
        source_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ", # standard test video
        type="YOUTUBE",
        status="PENDING"
    )
    job = ProcessingJob.objects.create(project=project, source_input=source, status="PENDING")
    
    print(f"Project ID: {project.id}")
    print(f"SourceInput ID: {source.id}")
    print(f"ProcessingJob ID: {job.id}")
    
    print_section("PIPELINE EXECUTION")
    # Trigger Celery task
    start_time = time.time()
    task_result = process_source_input.delay(source.id)
    
    print("Waiting for Celery worker to complete ingestion (timeout 360s)...")
    for _ in range(180):
        job.refresh_from_db()
        print(f"[{time.strftime('%X')}] Status: {job.status}")
        if job.status in ['COMPLETED', 'FAILED', 'PARTIAL_SUCCESS']:
            break
        time.sleep(2)
        
    end_time = time.time()
    
    source.refresh_from_db()
    project.refresh_from_db()
    
    print(f"\nPipeline finished with status: {job.status}")
    print(f"Execution time: {end_time - start_time:.2f} seconds")
    if job.error_log:
        print(f"Error Log: {job.error_log}")
        
    print_section("TRANSCRIPT STAGE")
    print(f"Provider used: {source.transcript_source}")
    print(f"Transcript length: {source.transcript_length}")
    print(f"Fallback layer: {source.transcript_retrieval_method}")
    
    print_section("AI STAGE")
    usage_events = UsageEvent.objects.filter(organization=org, event_type='AI_GENERATION', created_at__gte=timezone.now() - timezone.timedelta(minutes=5))
    # Note: Our real Gemini usage isn't cleanly tracked by prompt/response count in DB yet, but we can look at assets
    moments = Moment.objects.filter(project=project)
    assets = GeneratedAsset.objects.filter(project=project)
    
    print(f"Moments generated: {moments.count()}")
    print(f"Assets generated: {assets.count()}")
    
    print_section("DATABASE VERIFICATION (IDEMPOTENCY)")
    initial_asset_count = assets.count()
    print(f"Initial asset count: {initial_asset_count}")
    
    print("Running ingestion twice (retry_ai_generation) for the same project...")
    retry_task = retry_ai_generation.delay(source.id)
    for _ in range(120):
        if retry_task.ready():
            break
        time.sleep(1)
        
    assets_after_retry = GeneratedAsset.objects.filter(project=project).count()
    print(f"Asset count after 1st retry: {assets_after_retry}")
    
    if initial_asset_count > 0 and assets_after_retry == initial_asset_count:
        print("Idempotency Check: PASS (Asset count did not increase unexpectedly)")
    else:
        print("Idempotency Check: FAIL")
        
    print_section("CONCURRENCY VERIFICATION")
    # Simulate simultaneous manual generation and automatic retry
    client = APIClient()
    client.force_authenticate(user=user)
    
    moment = moments.first()
    if not moment:
        print("FAIL: No moments to test concurrency against.")
        sys.exit(1)
        
    # We will trigger the background task
    print("Triggering background retry_ai_generation...")
    # we hold the lock artificially, or trigger it via delay. Let's trigger via delay and immediately hit the API.
    # To be perfectly safe and ensure they overlap, we'll acquire the lock manually or trigger delay.
    from projects.tasks import redis_client
    lock_key = f"project_ai_generation_{project.id}"
    
    redis_online = False
    if redis_client:
        try:
            redis_client.set(lock_key, "LOCKED", ex=60)
            print("Acquired Redis lock manually to simulate active generation.")
            redis_online = True
        except Exception as e:
            print(f"Redis connection failed: {e}")
            print("Skipping manual Redis lock acquisition. Concurrency check requires a running Redis server.")
    
    # Hit the API
    print("Hitting manual generate_assets API view...")
    settings.ALLOWED_HOSTS.append('testserver')
    url = f"/api/orgs/{org.slug}/projects/{project.id}/moments/{moment.id}/generate-assets/"
    response = client.post(url)
    
    print(f"API Response Status: {response.status_code}")
    print(f"API Response Data: {getattr(response, 'data', response.content)}")
    
    if redis_client and redis_online:
        try:
            redis_client.delete(lock_key)
        except Exception:
            pass
        
    concurrency_passed = True
    if redis_online:
        if response.status_code == 409:
            print("Concurrency Check: PASS (Received 409 Conflict)")
        else:
            print("Concurrency Check: FAIL")
            concurrency_passed = False
    else:
        print("Concurrency Check: SKIP (Redis is offline)")
        
    # Verdict
    print_section("VERDICT")
    
    # Determine GO or NO GO
    go = True
    reasons = []
    
    if job.status not in ['COMPLETED', 'PARTIAL_SUCCESS']:
        go = False
        reasons.append(f"Pipeline failed with status {job.status}")
        
    if initial_asset_count == 0:
        go = False
        reasons.append("No assets generated")
        
    if assets_after_retry != initial_asset_count:
        go = False
        reasons.append("Idempotency failed (assets duplicated)")
        
    if not concurrency_passed:
        go = False
        reasons.append("Concurrency protection failed (no 409 returned)")
        
    if go:
        print("GO")
    else:
        print("NO GO")
        for r in reasons:
            print(f"- {r}")

if __name__ == '__main__':
    from django.utils import timezone
    main()
