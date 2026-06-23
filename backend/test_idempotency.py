import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viralops.settings')
os.environ['DJANGO_TEST'] = '1'
django.setup()

from projects.models import Project, SourceInput, GeneratedAsset
from projects.tasks import retry_ai_generation, process_source_input
from rest_framework.test import APIClient
from django.urls import reverse

def run_test():
    # Setup test project
    project = Project.objects.first()
    if not project:
        print("No project found to test.")
        return
        
    source = project.sources.first()
    if not source:
        print("No source found.")
        return

    print(f"Testing on Project {project.id} with Source {source.id}")

    # Set project status to RETRYING for manual protection test
    project.status = 'RETRYING'
    project.save()

    print("\n--- Test: Manual Retry Protection ---")
    try:
        from projects.views import ProjectViewSet
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.post('/fake-url/')
        view = ProjectViewSet.as_view({'post': 'retry'})
        response = view(request, pk=project.id)
        print(f"Manual Retry Response Status: {response.status_code}")
        print(f"Manual Retry Response Data: {response.data}")
    except Exception as e:
        print(f"Manual Retry Error: {e}")

    # Test asset deduplication
    print("\n--- Test: Asset Deduplication ---")
    project.status = 'PENDING'
    project.save()
    
    initial_asset_count = GeneratedAsset.objects.filter(project=project).count()
    print(f"Initial Asset Count: {initial_asset_count}")
    
    # Run process_source_input
    print("1. Running process_source_input (simulating initial ingestion)")
    try:
        process_source_input(source.id)
    except Exception as e:
        print(f"Exception during ingestion: {type(e).__name__} - {e}")

    # Count assets after initial run
    initial_asset_count = GeneratedAsset.objects.filter(project=project).count()
    print(f"   Initial Generated Assets: {initial_asset_count}")

    print("\n2. Running retry_ai_generation (simulating first retry)")
    try:
        retry_ai_generation(project.id)
    except Exception as e:
        print(f"Exception during first retry: {type(e).__name__} - {e}")
        
    # Count assets after first retry
    retry1_asset_count = GeneratedAsset.objects.filter(project=project).count()
    print(f"   Generated Assets after Retry 1: {retry1_asset_count}")

    print("\n3. Running retry_ai_generation (simulating second retry)")
    try:
        retry_ai_generation(project.id)
    except Exception as e:
        print(f"Exception during second retry: {type(e).__name__} - {e}")
        
    count_after_second = GeneratedAsset.objects.filter(project=project).count()
    print(f"   Generated Assets after Retry 2: {count_after_second}")
    
    if initial_asset_count > 0 and initial_asset_count == count_after_second:
        print("SUCCESS: No duplicates created.")
    else:
        print("FAILED: Duplicates created or no assets generated.")

    print("\n--- Test: Race Condition / Locking ---")
    # We will simulate a lock being held
    from projects.tasks import redis_client
    lock_key = f"project_ai_generation_{project.id}"
    if redis_client:
        try:
            redis_client.set(lock_key, "LOCKED", ex=60)
            print("Simulated active lock acquired.")
            
            # Try running while locked
            print("Running process_source_input while locked...")
            process_source_input(source.id)
            
            redis_client.delete(lock_key)
            print("Lock released.")
        except Exception as e:
            print(f"Skipping lock test due to Redis error: {e}")
    else:
        print("Redis client not available.")

if __name__ == '__main__':
    run_test()
