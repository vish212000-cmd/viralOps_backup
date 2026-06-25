from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Profile, SocialLinks, CreatorProfile, UserPreferences,
    BrandDefaults, NotificationSettings, SecuritySettings,
    ConnectedAccounts, APIToken, SessionHistory
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'username']
        read_only_fields = ['id', 'email', 'username']


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        exclude = ['id', 'user', 'created_at', 'updated_at']


class SocialLinksSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialLinks
        exclude = ['id', 'user', 'created_at', 'updated_at']


class CreatorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreatorProfile
        exclude = ['id', 'user', 'created_at', 'updated_at']


class UserPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreferences
        exclude = ['id', 'user', 'created_at', 'updated_at']


class BrandDefaultsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandDefaults
        exclude = ['id', 'user', 'created_at', 'updated_at']


class NotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSettings
        exclude = ['id', 'user', 'created_at', 'updated_at']


class SecuritySettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecuritySettings
        exclude = ['id', 'user', 'created_at', 'updated_at']


class ConnectedAccountsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConnectedAccounts
        fields = ['id', 'provider', 'last_sync', 'created_at']
        read_only_fields = ['id', 'provider', 'last_sync', 'created_at']


class APITokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIToken
        fields = ['id', 'name', 'prefix', 'scopes', 'last_used', 'expires_at', 'created_at']
        read_only_fields = ['id', 'prefix', 'last_used', 'created_at']


class SessionHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionHistory
        fields = ['id', 'device', 'browser', 'os', 'location', 'ip_address', 'is_active', 'created_at', 'last_activity']
        read_only_fields = ['id', 'device', 'browser', 'os', 'location', 'ip_address', 'created_at', 'last_activity']


class FullAccountSerializer(serializers.ModelSerializer):
    user = UserSerializer(source='*')
    profile = ProfileSerializer()
    social_links = SocialLinksSerializer(required=False)
    creator_profile = CreatorProfileSerializer(required=False)
    preferences = UserPreferencesSerializer(required=False)
    brand_defaults = BrandDefaultsSerializer(required=False)
    notification_settings = NotificationSettingsSerializer(required=False)
    security_settings = SecuritySettingsSerializer(required=False)
    
    class Meta:
        model = User
        fields = [
            'user', 'profile', 'social_links', 'creator_profile',
            'preferences', 'brand_defaults', 'notification_settings',
            'security_settings'
        ]

    def update(self, instance, validated_data):
        # Handle user fields from root (due to source='*')
        user_fields = ['first_name', 'last_name']
        user_updated = False
        for attr in user_fields:
            if attr in validated_data:
                setattr(instance, attr, validated_data.pop(attr))
                user_updated = True
        
        # Also check if it was nested under 'user' for safety
        user_data = validated_data.pop('user', {})
        if user_data:
            for attr, value in user_data.items():
                setattr(instance, attr, value)
            user_updated = True
            
        if user_updated:
            instance.save()

        # Handle nested one-to-one relations
        nested_fields = [
            ('profile', ProfileSerializer),
            ('social_links', SocialLinksSerializer),
            ('creator_profile', CreatorProfileSerializer),
            ('preferences', UserPreferencesSerializer),
            ('brand_defaults', BrandDefaultsSerializer),
            ('notification_settings', NotificationSettingsSerializer),
            ('security_settings', SecuritySettingsSerializer),
        ]

        for field_name, serializer_class in nested_fields:
            if field_name in validated_data:
                field_data = validated_data.pop(field_name)
                # Ensure the related object exists, otherwise create it
                related_obj = getattr(instance, field_name, None)
                if not related_obj:
                    related_model = serializer_class.Meta.model
                    related_obj = related_model(user=instance)
                
                for attr, value in field_data.items():
                    setattr(related_obj, attr, value)
                related_obj.save()

        return instance
