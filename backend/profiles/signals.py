from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import (
    Profile, CreatorProfile, UserPreferences,
    BrandDefaults, NotificationSettings, SecuritySettings
)

User = settings.AUTH_USER_MODEL

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        CreatorProfile.objects.create(user=instance)
        UserPreferences.objects.create(user=instance)
        BrandDefaults.objects.create(user=instance)
        NotificationSettings.objects.create(user=instance)
        SecuritySettings.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
    if hasattr(instance, 'creator_profile'):
        instance.creator_profile.save()
    if hasattr(instance, 'preferences'):
        instance.preferences.save()
    if hasattr(instance, 'brand_defaults'):
        instance.brand_defaults.save()
    if hasattr(instance, 'notification_settings'):
        instance.notification_settings.save()
    if hasattr(instance, 'security_settings'):
        instance.security_settings.save()
