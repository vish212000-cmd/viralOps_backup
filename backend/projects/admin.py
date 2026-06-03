from django.contrib import admin
from .models import (
    Project, SourceInput, TranscriptRecord, ProcessingJob,
    GeneratedAsset, GeneratedAssetVersion, Template, MemoryRecord,
    UsageEvent, AuditLog
)

admin.site.register(Project)
admin.site.register(SourceInput)
admin.site.register(TranscriptRecord)
admin.site.register(ProcessingJob)
admin.site.register(GeneratedAsset)
admin.site.register(GeneratedAssetVersion)
admin.site.register(Template)
admin.site.register(MemoryRecord)
admin.site.register(UsageEvent)
admin.site.register(AuditLog)
