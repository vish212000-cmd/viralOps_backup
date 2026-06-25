import uuid
from django.db import models
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.utils.translation import gettext_lazy as _

User = settings.AUTH_USER_MODEL

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    banner = models.ImageField(upload_to='banners/', blank=True, null=True)
    
    display_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    country = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    timezone = models.CharField(max_length=100, default='UTC')
    language = models.CharField(max_length=10, default='en')
    
    job_title = models.CharField(max_length=255, blank=True)
    company = models.CharField(max_length=255, blank=True)
    website = models.URLField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} Profile"


class SocialLinks(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='social_links')
    linkedin = models.URLField(max_length=255, blank=True)
    twitter = models.URLField(max_length=255, blank=True)
    youtube = models.URLField(max_length=255, blank=True)
    instagram = models.URLField(max_length=255, blank=True)
    tiktok = models.URLField(max_length=255, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class CreatorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='creator_profile')
    industry = models.CharField(max_length=100, blank=True)
    role = models.CharField(max_length=100, blank=True)
    niche = models.CharField(max_length=100, blank=True) # Business, Education, Finance, etc.
    content_niches = models.JSONField(default=list, blank=True)
    audience_size = models.CharField(max_length=50, blank=True)
    primary_platform = models.CharField(max_length=50, blank=True)
    content_frequency = models.CharField(max_length=50, blank=True)
    preferred_tone = models.CharField(max_length=100, blank=True)
    preferred_language = models.CharField(max_length=100, blank=True)
    brand_voice = models.TextField(blank=True)
    default_cta = models.TextField(blank=True)
    target_audience = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class UserPreferences(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    default_ai_provider = models.CharField(max_length=50, default='OpenAI')
    preferred_model = models.CharField(max_length=50, blank=True)
    temperature = models.FloatField(default=0.7)
    creativity_level = models.CharField(max_length=50, default='Balanced')
    default_output_language = models.CharField(max_length=10, default='en')
    caption_style = models.CharField(max_length=50, blank=True)
    hook_style = models.CharField(max_length=50, blank=True)
    title_style = models.CharField(max_length=50, blank=True)
    emoji_preference = models.CharField(max_length=50, default='moderate')
    hashtag_preference = models.CharField(max_length=50, default='moderate')
    default_output_formats = models.JSONField(default=list, blank=True) # ['YouTube', 'Instagram', 'TikTok']
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class BrandDefaults(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='brand_defaults')
    brand_colors = models.JSONField(default=list, blank=True)
    logo = models.ImageField(upload_to='brand_logos/', blank=True, null=True)
    watermark = models.ImageField(upload_to='brand_watermarks/', blank=True, null=True)
    fonts = models.JSONField(default=list, blank=True)
    brand_voice = models.TextField(blank=True)
    default_intro = models.TextField(blank=True)
    default_outro = models.TextField(blank=True)
    default_cta = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class NotificationSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_settings')
    email_notifications = models.BooleanField(default=True)
    desktop_notifications = models.BooleanField(default=False)
    
    processing_complete = models.BooleanField(default=True)
    asset_ready = models.BooleanField(default=True)
    billing = models.BooleanField(default=True)
    product_updates = models.BooleanField(default=True)
    security_alerts = models.BooleanField(default=True)
    weekly_reports = models.BooleanField(default=False)
    marketing_emails = models.BooleanField(default=False)
    
    sms_notifications = models.BooleanField(default=False)
    push_notifications = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class SecuritySettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='security_settings')
    phone_verified = models.BooleanField(default=False)
    recovery_codes = models.JSONField(default=list, blank=True)
    last_password_change = models.DateTimeField(auto_now_add=True)
    failed_login_attempts = models.IntegerField(default=0)
    trusted_devices = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ConnectedAccounts(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connected_accounts')
    provider = models.CharField(max_length=50) # Google, GitHub, Microsoft, Apple, LinkedIn
    provider_account_id = models.CharField(max_length=255)
    access_token = models.TextField(blank=True)
    refresh_token = models.TextField(blank=True)
    last_sync = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'provider')


class APIToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_tokens')
    name = models.CharField(max_length=255)
    prefix = models.CharField(max_length=8)
    token_hash = models.CharField(max_length=128)
    scopes = models.JSONField(default=list, blank=True)
    last_used = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    webhook_secret = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def set_token(self, raw_token):
        self.prefix = raw_token[:8]
        self.token_hash = make_password(raw_token)
        
    def check_token(self, raw_token):
        return check_password(raw_token, self.token_hash)


class SessionHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='session_history')
    session_id = models.CharField(max_length=255, db_index=True)
    device = models.CharField(max_length=255, blank=True)
    browser = models.CharField(max_length=255, blank=True)
    os = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    timezone = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)

    def terminate(self):
        self.is_active = False
        self.save()
