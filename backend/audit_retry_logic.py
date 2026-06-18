import os
import django
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "viralops.settings")
django.setup()

from django.contrib.auth import get_user_model
from organizations.models import Organization, Membership
from projects.models import Project, SourceInput, ProcessingJob
from projects.tasks import process_source_input
from celery.exceptions import Retry
from rest_framework.test import APIClient
from django.utils import timezone
from unittest.mock import patch
from google.api_core.exceptions import ResourceExhausted

User = get_user_model()

def run_audit():
    print("===========================================")
    print(" RETRY VERIFICATION AUDIT - VIRALOPS ")
    print("===========================================\n")

    # 1. Setup Data
    user, _ = User.objects.get_or_create(username="retry_auditor", email="retry@example.com")
    org, _ = Organization.objects.get_or_create(name="Retry Org", slug="retry-org")
    if not Membership.objects.filter(user=user, organization=org).exists():
        Membership.objects.create(user=user, organization=org, role='ADMIN')
    
    Project.objects.filter(organization=org).delete()

    project = Project.objects.create(organization=org, name="Retry Test Project")
    source = SourceInput.objects.create(
        project=project, type="YOUTUBE", source_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    
    print("--- 1. Initial State ---")
    print(f"Project Status: {project.status}")
    print(f"SourceInput Status: {source.status}")
    print(f"ProcessingJob: None initially\n")

    # Mock the Gemini call to raise ResourceExhausted immediately so we don't wait for actual API
    # (Though we are out of quota anyway, this makes it instant and robust).
    with patch('projects.ai_provider.GeminiProvider.generate_social_assets') as mock_generate:
        mock_generate.side_effect = ResourceExhausted("429 Quota exceeded")

        # --- Attempt 1 ---
        print("--- 2. First execution (Attempt 1) ---")
        try:
            # We must bind mock request to task so it can read max_retries
            process_source_input.request.retries = 0
            process_source_input(source.id)
            print("ERROR: Did not raise Retry")
        except Exception as e:
            project.refresh_from_db()
            source.refresh_from_db()
            job = ProcessingJob.objects.get(source_input=source)
            
            print(f"Project status: {project.status}")
            print(f"Source status: {source.status}")
            print(f"Job status: {job.status}")
            print(f"Job retry_count: {job.retry_count}")
            print(f"Job error_message: {job.error_message}")
            print(f"Caught Exception: {type(e).__name__}")

        print("\n--- 3. Second execution (Attempt 2) ---")
        try:
            process_source_input.request.retries = 1
            process_source_input(source.id)
            print("ERROR: Did not raise Retry")
        except Exception as e:
            project.refresh_from_db()
            job.refresh_from_db()
            print(f"Project status: {project.status}")
            print(f"Job status: {job.status}")
            print(f"Job retry_count: {job.retry_count}")
            print(f"Caught Exception: {str(e)}")

        print("\n--- 4. Third execution (Attempt 3) ---")
        try:
            process_source_input.request.retries = 2
            process_source_input(source.id)
            print("ERROR: Did not raise Retry")
        except Exception as e:
            project.refresh_from_db()
            job.refresh_from_db()
            print(f"Project status: {project.status}")
            print(f"Job status: {job.status}")
            print(f"Job retry_count: {job.retry_count}")
            print(f"Caught Exception: {str(e)}")

        print("\n--- 5. Fourth execution (Final Attempt - Exhausted) ---")
        try:
            process_source_input.request.retries = 3
            process_source_input(source.id)
            print("ERROR: Did not fail or raise exception!")
        except Exception as e:
            project.refresh_from_db()
            source.refresh_from_db()
            job.refresh_from_db()
            print(f"Project status: {project.status}")
            print(f"Source status: {source.status}")
            print(f"Job status: {job.status}")
            print(f"Job retry_count: {job.retry_count}")
            print(f"Caught Exception: {type(e).__name__}")

    print("\n--- 6. API Verification ---")
    from projects.serializers import ProjectSerializer
    serializer = ProjectSerializer(project)
    data = serializer.data
    print(f"API Serialization Success")
    print(f"retry_count: {data.get('retry_count')}")
    print(f"last_retry_at: {data.get('last_retry_at')}")
    print(f"error_message: {data.get('error_message')}")
    print(f"status: {data.get('status')}")

if __name__ == "__main__":
    run_audit()
