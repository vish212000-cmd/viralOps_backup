from rest_framework import serializers
from django.contrib.auth import get_user_model
from organizations.models import Organization, Membership, BrandKit
from .models import (
    Project, SourceInput, TranscriptRecord, ProcessingJob,
    GeneratedAsset, GeneratedAssetVersion, Template, MemoryRecord,
    UsageEvent, AuditLog, SocialPublishRecord,
    Moment, ContentIntelligenceRecord, TranscriptSegment,
)

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')

class BrandKitSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandKit
        fields = ('id', 'brand_name', 'brand_voice', 'audience', 'cta', 'hashtags', 'examples', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

class OrganizationSerializer(serializers.ModelSerializer):
    brand_kit = BrandKitSerializer(read_only=True)

    class Meta:
        model = Organization
        fields = ('id', 'name', 'slug', 'brand_kit', 'created_at')
        read_only_fields = ('slug',)

class MembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    organization = OrganizationSerializer(read_only=True)
    
    class Meta:
        model = Membership
        fields = ('id', 'user', 'organization', 'role', 'joined_at')

class ProjectSerializer(serializers.ModelSerializer):
    error_message = serializers.SerializerMethodField()
    error_type = serializers.SerializerMethodField()
    failing_step = serializers.SerializerMethodField()
    retry_count = serializers.SerializerMethodField()
    last_retry_at = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ('id', 'organization', 'name', 'description', 'status', 'error_message', 'error_type', 'failing_step', 'retry_count', 'last_retry_at', 'created_at', 'updated_at')
        read_only_fields = ('organization',)

    def get_error_message(self, obj):
        latest_job = obj.jobs.order_by('-created_at').first()
        return latest_job.error_message if latest_job else None

    def get_error_type(self, obj):
        latest_job = obj.jobs.order_by('-created_at').first()
        return latest_job.error_type if latest_job else None

    def get_failing_step(self, obj):
        latest_job = obj.jobs.order_by('-created_at').first()
        return latest_job.failing_step if latest_job else None

    def get_retry_count(self, obj):
        latest_job = obj.jobs.order_by('-created_at').first()
        return latest_job.retry_count if latest_job else 0

    def get_last_retry_at(self, obj):
        latest_job = obj.jobs.order_by('-created_at').first()
        return latest_job.last_retry_at if latest_job else None

    def validate_name(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Project name must be at least 3 characters long.")
        return value.strip()

class SourceInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceInput
        fields = (
            'id', 'project', 'type', 'title', 'source_url', 'file_name',
            'file_size', 'file', 'text_content', 'status', 'error_message',
            # Transcript diagnostics
            'transcript_source', 'transcript_length', 'transcript_validation_status',
            'transcript_retrieval_method', 'transcript_retrieved_at', 'transcript_preview',
            'created_at', 'updated_at'
        )
        read_only_fields = (
            'project', 'status', 'error_message',
            'transcript_source', 'transcript_length', 'transcript_validation_status',
            'transcript_retrieval_method', 'transcript_retrieved_at', 'transcript_preview',
        )

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


class TranscriptSegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TranscriptSegment
        fields = ('id', 'transcript_record', 'start_time', 'end_time', 'text', 'speaker', 'segment_index', 'created_at')

class TranscriptRecordSerializer(serializers.ModelSerializer):
    segment_list = TranscriptSegmentSerializer(many=True, read_only=True)

    class Meta:
        model = TranscriptRecord
        fields = ('id', 'source_input', 'raw_text', 'normalized_text', 'segments', 'segment_list', 'created_at')

class ProcessingJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessingJob
        fields = ('id', 'task_id', 'source_input', 'project', 'status', 'error_log', 'error_type', 'error_message', 'failing_step', 'retry_count', 'last_retry_at', 'created_at', 'updated_at')

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
        fields = ('id', 'project', 'type', 'platform', 'content', 'metadata', 'is_favorite', 'moment', 'created_at', 'updated_at', 'versions', 'publish_records')
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


class MomentSerializer(serializers.ModelSerializer):
    segments = TranscriptSegmentSerializer(many=True, read_only=True)
    generated_assets = GeneratedAssetSerializer(many=True, read_only=True)

    class Meta:
        model = Moment
        fields = (
            'id', 'project', 'source_input', 'title', 'category', 'score',
            'start_time', 'end_time', 'excerpt', 'metadata', 'is_favorite',
            'video_clip_url', 'segments', 'generated_assets',
            'created_at', 'updated_at',
        )
        read_only_fields = ('project', 'source_input', 'score', 'metadata', 'segments', 'generated_assets')


class ContentIntelligenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentIntelligenceRecord
        fields = (
            'id', 'project', 'source_input', 'summary', 'topics', 'keywords',
            'entities', 'emotional_moments', 'viral_score', 'created_at', 'updated_at',
        )
        read_only_fields = ('project', 'source_input')
