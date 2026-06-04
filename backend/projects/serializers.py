from rest_framework import serializers
from django.contrib.auth import get_user_model
from organizations.models import Organization, Membership
from .models import (
    Project, SourceInput, TranscriptRecord, ProcessingJob,
    GeneratedAsset, GeneratedAssetVersion, Template, MemoryRecord,
    UsageEvent, AuditLog, SocialPublishRecord
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
            'file_size', 'file', 'text_content', 'status', 'error_message', 'created_at', 'updated_at'
        )
        read_only_fields = ('project', 'status', 'error_message')

    def validate(self, data):
        stype = data.get('type')
        uploaded_file = data.get('file')
        
        if uploaded_file:
            if uploaded_file.size > 52428800:
                raise serializers.ValidationError({"file": "File size exceeds the maximum 50MB limit."})
            
            name = uploaded_file.name.lower()
            if stype == 'VIDEO':
                if not (name.endswith('.mp4') or name.endswith('.mov') or name.endswith('.avi') or name.endswith('.mkv') or name.endswith('.webm')):
                    raise serializers.ValidationError({"file": "Unsupported video file extension."})
            elif stype == 'AUDIO':
                if not (name.endswith('.mp3') or name.endswith('.wav') or name.endswith('.m4a') or name.endswith('.aac') or name.endswith('.flac')):
                    raise serializers.ValidationError({"file": "Unsupported audio file extension."})
            elif stype == 'PDF':
                if not name.endswith('.pdf'):
                    raise serializers.ValidationError({"file": "Only PDF files are allowed for PDF source inputs."})
            else:
                raise serializers.ValidationError({"file": "Files can only be uploaded for VIDEO, AUDIO, or PDF source inputs."})

        if stype == 'YOUTUBE':
            url = data.get('source_url', '')
            if not url or not (url.startswith('https://') or url.startswith('http://')):
                raise serializers.ValidationError({"source_url": "A valid YouTube URL must be provided."})
                
        elif stype in ['VIDEO', 'AUDIO']:
            if not uploaded_file and not data.get('file_name'):
                raise serializers.ValidationError({"file_name": "A file or file_name is required for video/audio sources."})
                
        elif stype in ['ARTICLE', 'TRANSCRIPT', 'SCRIPT']:
            text = data.get('text_content', '').strip()
            url = data.get('source_url', '').strip()
            if stype == 'ARTICLE' and url:
                pass
            elif not text:
                raise serializers.ValidationError({"text_content": "Text content cannot be empty for text-based sources."})
                
        elif stype == 'PDF':
            if not uploaded_file and not data.get('text_content', '').strip():
                raise serializers.ValidationError({"text_content": "Either a PDF file upload or text content is required."})

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

class SocialPublishRecordSerializer(serializers.ModelSerializer):
    published_by_username = serializers.CharField(source='published_by.username', read_only=True)

    class Meta:
        model = SocialPublishRecord
        fields = ('id', 'asset', 'platform', 'status', 'published_url', 'error_message', 'published_by', 'published_by_username', 'created_at', 'updated_at')
        read_only_fields = ('published_by', 'status', 'published_url', 'error_message')

class GeneratedAssetSerializer(serializers.ModelSerializer):
    versions = GeneratedAssetVersionSerializer(many=True, read_only=True)
    publish_records = SocialPublishRecordSerializer(many=True, read_only=True)

    class Meta:
        model = GeneratedAsset
        fields = ('id', 'project', 'type', 'platform', 'content', 'metadata', 'is_favorite', 'created_at', 'updated_at', 'versions', 'publish_records')
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
