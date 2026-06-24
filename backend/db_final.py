
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "viralops.settings.local")
django.setup()
from projects.models import Project, SourceInput, ProcessingJob, TranscriptRecord, Moment, GeneratedAsset, ContentIntelligenceRecord
p = Project.objects.get(id="183")
print(f"Project ID:              {p.id}")
print(f"Project Status:          {p.status}")
src = p.sources.first()
if src:
    print(f"SourceInput ID:          {src.id}")
    print(f"SourceInput Status:      {src.status}")
    print(f"TranscriptRecord Count:  {TranscriptRecord.objects.filter(source_input=src).count()}")
print(f"ContentIntelligenceRecord Count: {ContentIntelligenceRecord.objects.filter(project=p).count()}")
job = ProcessingJob.objects.filter(project=p).first()
if job:
    print(f"ProcessingJob ID:        {job.id}")
    print(f"ProcessingJob Status:    {job.status}")
else: print("ProcessingJob: NOT FOUND")
print(f"Moment Count:            {Moment.objects.filter(project=p).count()}")
print(f"GeneratedAsset Count:    {GeneratedAsset.objects.filter(project=p).count()}")
print("ASSET EVIDENCE - First 5 assets:")
for a in GeneratedAsset.objects.filter(project=p).order_by("id")[:5]:
    print(f"  Asset ID: {a.id} | Type: {a.type} | Preview: {(a.content or '')[:80].replace(chr(10),' ')}")
print("Asset breakdown:")
for t in ["HOOK","TITLE","CAPTION","CTA","HASHTAG","SCRIPT","THREAD","LINKEDIN","TWEET","THUMBNAIL"]:
    cnt = GeneratedAsset.objects.filter(project=p, type=t).count()
    if cnt: print(f"  {t}: {cnt}")
