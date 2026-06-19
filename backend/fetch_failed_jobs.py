import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viralops.settings.local')
django.setup()

from projects.models import ProcessingJob, SourceInput, Project

failed_jobs = ProcessingJob.objects.filter(status='FAILED')

print(f"Found {failed_jobs.count()} failed jobs.")

for job in failed_jobs:
    print("================================")
    print(f"Project ID: {job.project_id}")
    print(f"ProcessingJob ID: {job.id}")
    print(f"SourceInput ID: {job.source_input_id}")
    print("--- Error Log ---")
    print(job.error_log)
    print("--- SourceInput Error Message ---")
    print(job.source_input.error_message)
    print("================================")
