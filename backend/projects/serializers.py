from rest_framework import serializers
from django.contrib.auth import get_user_model
from organizations.models import Organization, Membership
from .models import (
    Project, SourceInput, TranscriptRecord, ProcessingJob,
    GeneratedAsset, GeneratedAssetVersion, Template, MemoryRecord,
    UsageEvent, AuditLog
)

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ('id', 'name', 'slug', 'created_at')

class MembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    organization = OrganizationSerializer(read_only=True)
    
    class Meta:
        model = Membership
        fields = ('id', 'user', 'organization', 'role', 'joined_at')

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ('id', 'organization', 'name', 'description', 'status', 'created_at', 'updated_at')
        read_only_fields = ('organization',)

    def validate_name(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Project name must be at least 3 characters long.")
        return value.strip()

class SourceInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceInput
        fields = (
            'id', 'project', 'type', 'title', 'source_url', 'file_name', 
            'file_size', 'text_content', 'status', 'error_message', 'created_at', 'updated_at'
        )
        read_only_fields = ('project', 'status', 'error_message')

    def validate(self, data):
        stype = data.get('type')
        
        if stype == 'YOUTUBE':
            url = data.get('source_url', '')
            if not url or not (url.startswith('https://') or url.startswith('http://')):
                raise serializers.ValidationError({"source_url": "A valid YouTube URL must be provided."})
                
        elif stype in ['VIDEO', 'AUDIO']:
            file_size = data.get('file_size')
            if file_size and file_size > 52428800:
                raise serializers.ValidationError({"file_size": "File size exceeds the maximum 50MB limit."})
                
        elif stype in ['ARTICLE', 'TRANSCRIPT', 'SCRIPT', 'PDF']:
            text = data.get('text_content', '').strip()
            if not text:
                raise serializers.ValidationError({"text_content": "Text content cannot be empty for text-based sources."})
                
        return data


class TranscriptRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = TranscriptRecord
        fields = ('id', 'source_input', 'raw_text', 'normalized_text', 'segments', 'created_at')

class ProcessingJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessingJob
        fields = ('id', 'task_id', 'source_input', 'project', 'status', 'error_log', 'created_at', 'updated_at')

class GeneratedAssetVersionSerializer(serializers.ModelSerializer):
    edited_by_username = serializers.CharField(source='edited_by.username', read_only=True)

    class Meta:
        model = GeneratedAssetVersion
        fields = ('id', 'asset', 'content', 'edited_by', 'edited_by_username', 'created_at')
        read_only_fields = ('edited_by',)

class GeneratedAssetSerializer(serializers.ModelSerializer):
    versions = GeneratedAssetVersionSerializer(many=True, read_only=True)

    class Meta:
        model = GeneratedAsset
        fields = ('id', 'project', 'type', 'platform', 'content', 'metadata', 'is_favorite', 'created_at', 'updated_at', 'versions')
        read_only_fields = ('project',)

class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = ('id', 'organization', 'name', 'type', 'content', 'created_at')
        read_only_fields = ('organization',)

class MemoryRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemoryRecord
        fields = ('id', 'organization', 'key', 'value', 'updated_at')
        read_only_fields = ('organization',)

class UsageEventSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = UsageEvent
        fields = ('id', 'organization', 'user', 'username', 'event_type', 'quantity', 'created_at')

class AuditLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = AuditLog
        fields = ('id', 'organization', 'user', 'username', 'action', 'details', 'ip_address', 'created_at')
