import os, sys, django
sys.path.append('c:/personal/projects/viralOps/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viralops.settings.local')
django.setup()
from projects.models import ProcessingJob, SourceInput

for j_id in [73, 74, 75, 76]:
    j = ProcessingJob.objects.get(id=j_id)
    s = j.source_input
    print(f"Job ID: {j.id}, Project ID: {j.project.id}, SourceInput ID: {s.id}")
    print(f"Source Type: {s.type}, status: {s.status}, validation: {s.transcript_validation_status}")
    print(f"Method: {s.transcript_retrieval_method}, Source: {s.transcript_source}")
    print(f"Asset count: {j.project.assets.count()}")
    print("-------------------------")
