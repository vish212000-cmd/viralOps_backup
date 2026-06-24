
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viralops.settings.local')
django.setup()
from projects.models import Project, SourceInput, ProcessingJob, TranscriptRecord, Moment, GeneratedAsset
p = Project.objects.get(id='180')
print(f"Project ID: {p.id}")
src = p.sources.first()
if src:
    print(f"SourceInput ID: {src.id}")
    print(f"TranscriptRecord count: {TranscriptRecord.objects.filter(source_input=src).count()}")
job = ProcessingJob.objects.filter(project=p).first()
if job:
    print(f"ProcessingJob ID: {job.id}")
print(f"Moment count: {Moment.objects.filter(project=p).count()}")
print(f"GeneratedAsset count: {GeneratedAsset.objects.filter(project=p).count()}")
hooks = GeneratedAsset.objects.filter(project=p, type='HOOK').count()
titles = GeneratedAsset.objects.filter(project=p, type='TITLE').count()
print("Actual generated assets:")
print(f"- Hooks: {hooks}")
print(f"- Titles: {titles}")
