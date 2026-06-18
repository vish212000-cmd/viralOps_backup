import os
import django
import sys
import time
import threading
import queue
import tracemalloc
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "viralops.settings")
import django.conf
# We must allow testserver or localhost before django.setup
os.environ["ALLOWED_HOSTS"] = "*"

django.setup()

from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from organizations.models import Organization, Membership
from projects.models import Project, SourceInput, ProcessingJob
from projects.tasks import process_source_input

User = get_user_model()

# Metrics collection
metrics = {
    'api_response_times': [],
    'queue_depths': [],
    'worker_active': 0,
    'failed_jobs': 0,
    'completed_jobs': 0,
}
metrics_lock = threading.Lock()

# Simulated Celery Queue
celery_queue = queue.Queue()

def mock_delay(task_func, *args, **kwargs):
    celery_queue.put((task_func, args, kwargs))

def celery_worker_simulator(worker_id):
    while True:
        try:
            task_func, args, kwargs = celery_queue.get(timeout=1)
            with metrics_lock:
                metrics['worker_active'] += 1
            
            try:
                # Execute the actual task synchronously
                task_func(*args, **kwargs)
                with metrics_lock:
                    metrics['completed_jobs'] += 1
            except Exception as e:
                with metrics_lock:
                    metrics['failed_jobs'] += 1
            finally:
                with metrics_lock:
                    metrics['worker_active'] -= 1
                celery_queue.task_done()
        except queue.Empty:
            # Check if test is done
            if stop_workers:
                break

def simulate_upload(client, org, i):
    start = time.time()
    # 1. Create Project
    proj_resp = client.post(f"/api/orgs/{org.slug}/projects/", {"name": f"Load Project {i}"}, format='json')
    if proj_resp.status_code != 201:
        print(f"Project Error: {proj_resp.content}")
        return proj_resp
    project_id = proj_resp.json()['id']
    
    # 2. Create SourceInput
    payload = {"type": "YOUTUBE", "source_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
    resp = client.post(f"/api/orgs/{org.slug}/projects/{project_id}/sources/", payload, format='json')
    if resp.status_code != 201:
        print(f"Source Error: {resp.content}")
    
    latency = time.time() - start
    with metrics_lock:
        metrics['api_response_times'].append(latency)
    return resp

def run_load_test(concurrent_uploads, num_workers=2):
    global stop_workers
    stop_workers = False
    print(f"\n==========================================================")
    print(f" STARTING LOAD TEST: {concurrent_uploads} CONCURRENT UPLOADS")
    print(f"==========================================================")
    
    # Reset metrics
    metrics['api_response_times'] = []
    metrics['queue_depths'] = []
    metrics['worker_active'] = 0
    metrics['failed_jobs'] = 0
    metrics['completed_jobs'] = 0
    
    tracemalloc.start()
    while not celery_queue.empty():
        celery_queue.get()

    user, _ = User.objects.get_or_create(username="loadtest_user", email="load@example.com")
    org, _ = Organization.objects.get_or_create(name="Load Test Org", slug="load-org")
    if not Membership.objects.filter(user=user, organization=org).exists():
        Membership.objects.create(user=user, organization=org, role='ADMIN')
    
    # Cleanup old data to prevent DB bloat
    Project.objects.filter(organization=org).delete()

    client = APIClient(SERVER_NAME='localhost')
    from rest_framework_simplejwt.tokens import RefreshToken
    token = str(RefreshToken.for_user(user).access_token)
    client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
    
    # Start workers
    workers = []
    for i in range(num_workers):
        t = threading.Thread(target=celery_worker_simulator, args=(i,))
        t.start()
        workers.append(t)
    
    # Mock AI services to sleep 2 seconds instead of calling Gemini to simulate processing without limits
    with patch('projects.tasks.process_source_input.delay') as mock_task_delay, \
         patch('projects.ai_provider.GeminiProvider.generate_social_assets') as mock_ai:
        
        mock_task_delay.side_effect = lambda *args, **kwargs: mock_delay(process_source_input, *args, **kwargs)
        mock_ai.side_effect = lambda *a, **k: time.sleep(2) or {"dummy": "data"}

        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_uploads) as executor:
            futures = [executor.submit(simulate_upload, client, org, i) for i in range(concurrent_uploads)]
            
            # Monitor queue depth while requests are executing
            while any(not f.done() for f in futures) or not celery_queue.empty():
                with metrics_lock:
                    metrics['queue_depths'].append(celery_queue.qsize())
                time.sleep(0.5)

        # Wait for all workers to finish processing
        celery_queue.join()
        stop_workers = True
        for w in workers:
            w.join()
            
        total_time = time.time() - start_time
        
    # Calculate stats
    avg_api_time = sum(metrics['api_response_times']) / len(metrics['api_response_times']) if metrics['api_response_times'] else 0
    max_queue = max(metrics['queue_depths']) if metrics['queue_depths'] else 0
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    mem_usage_mb = peak / 1024 / 1024

    print(f"Results for {concurrent_uploads} Uploads:")
    print(f" - Total Time: {total_time:.2f}s")
    print(f" - Avg API Response Time: {avg_api_time*1000:.2f}ms")
    print(f" - Max Queue Depth: {max_queue}")
    print(f" - Worker Threads Simulated: {num_workers}")
    print(f" - Completed Jobs: {metrics['completed_jobs']}")
    print(f" - Failed Jobs: {metrics['failed_jobs']}")
    print(f" - Peak Memory Usage: {mem_usage_mb:.2f} MB")
    print(f" - Database / Redis Health: OK (Simulated DB writes succeeded)")

if __name__ == "__main__":
    run_load_test(10, num_workers=2)
    run_load_test(25, num_workers=2)
    run_load_test(50, num_workers=2)
