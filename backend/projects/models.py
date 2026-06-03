from django.db import models
from django.conf import settings
from organizations.models import Organization

class Project(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('ARCHIVED', 'Archived'),
    ]
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.organization.name})"

class SourceInput(models.Model):
    TYPE_CHOICES = [
        ('VIDEO', 'Video Upload'),
        ('AUDIO', 'Audio Upload'),
        ('YOUTUBE', 'YouTube Link'),
        ('ARTICLE', 'Article/Blog Text'),
        ('TRANSCRIPT', 'Raw Transcript'),
        ('SCRIPT', 'Raw Script'),
        ('PDF', 'PDF Text'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending Ingestion'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='sources')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255, blank=True, default='')
    source_url = models.URLField(blank=True, default='')
    file_name = models.CharField(max_length=255, blank=True, default='')
    file_size = models.BigIntegerField(null=True, blank=True)
    text_content = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    error_message = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.type} - {self.title or self.file_name or 'Source'} ({self.project.name})"

class TranscriptRecord(models.Model):
    source_input = models.OneToOneField(SourceInput, on_delete=models.CASCADE, related_name='transcript')
    raw_text = models.TextField()
    normalized_text = models.TextField()
    segments = models.JSONField(default=list, help_text="List of JSON segments with start, end, speaker, text")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transcript for Source {self.source_input.id}"

class ProcessingJob(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    task_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    source_input = models.ForeignKey(SourceInput, on_delete=models.CASCADE, related_name='jobs')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='jobs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    error_log = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Job {self.task_id or 'Unassigned'} ({self.status})"

class GeneratedAsset(models.Model):
    TYPE_CHOICES = [
        ('HOOK', 'Hook Option'),
        ('TITLE', 'Title Variant'),
        ('CAPTION', 'Caption'),
        ('CTA', 'CTA Variant'),
        ('HASHTAG', 'Hashtag Set'),
        ('THUMBNAIL', 'Thumbnail Copy'),
        ('SCRIPT', 'Short Script'),
        ('PLATFORM_PACK', 'Platform Asset Bundle'),
    ]
    PLATFORM_CHOICES = [
        ('SHORTS', 'YouTube Shorts'),
        ('REELS', 'Instagram Reels'),
        ('TIKTOK', 'TikTok'),
        ('MULTI', 'Cross-Platform'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='assets')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default='MULTI')
    content = models.TextField(help_text="Standard content text or JSON string")
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional JSON metadata (e.g. timestamps, visual prompts)")
    is_favorite = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.type} ({self.platform}) - Project: {self.project.name}"

class GeneratedAssetVersion(models.Model):
    asset = models.ForeignKey(GeneratedAsset, on_delete=models.CASCADE, related_name='versions')
    content = models.TextField()
    edited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='edited_assets')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Version for Asset {self.asset.id} @ {self.created_at}"

class Template(models.Model):
    TYPE_CHOICES = [
        ('HOOK', 'Hook Template'),
        ('CTA', 'CTA Template'),
        ('SCRIPT', 'Script Format'),
    ]
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='templates')
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    content = models.TextField(help_text="Template structure with variables, e.g. 'How to {{action}} without {{pain}}'")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.type})"

class MemoryRecord(models.Model):
    KEY_CHOICES = [
        ('BRAND_TONE', 'Brand Tone & Voice'),
        ('STYLE_GUIDE', 'Style Guide'),
        ('PREFERRED_HOOKS', 'Preferred Hooks & Structures'),
        ('PAST_APPROVED_PATTERNS', 'Past Approved Patterns'),
    ]
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='memories')
    key = models.CharField(max_length=50, choices=KEY_CHOICES)
    value = models.JSONField(help_text="JSON payload containing configuration details")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('organization', 'key')

    def __str__(self):
        return f"{self.key} - {self.organization.name}"

class UsageEvent(models.Model):
    TYPE_CHOICES = [
        ('TRANSCRIPTION_MINUTES', 'Transcription Minutes'),
        ('AI_GENERATION', 'AI Content Generation'),
    ]
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='usage_events')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='usage_events')
    event_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    quantity = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event_type} ({self.quantity}) - Org: {self.organization.name}"

class AuditLog(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='audit_logs', null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=100)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        user_str = self.user.username if self.user else "System"
        return f"{user_str} performed {self.action} @ {self.created_at}"
