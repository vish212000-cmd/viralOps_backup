from django.http import HttpResponse
from rest_framework import viewsets, permissions, status, decorators, exceptions
from rest_framework.response import Response
from django.db import models
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.utils import timezone
from organizations.models import Organization, Membership
from organizations.permissions import IsOrganizationMember, IsOrganizationAdmin, IsSuperAdmin
from organizations.mixins import TenantScopedQuerysetMixin
from .models import (
    Project, SourceInput, TranscriptRecord, ProcessingJob,
    GeneratedAsset, GeneratedAssetVersion, Template, MemoryRecord,
    UsageEvent, AuditLog
)
from .serializers import (
    ProjectSerializer, SourceInputSerializer, TranscriptRecordSerializer,
    ProcessingJobSerializer, GeneratedAssetSerializer, GeneratedAssetVersionSerializer,
    TemplateSerializer, MemoryRecordSerializer, UsageEventSerializer, AuditLogSerializer,
    MembershipSerializer
)
from .tasks import process_source_input

User = get_user_model()

class ProjectViewSet(TenantScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Project.objects.all().select_related('organization').order_by('-created_at')
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrganizationMember]

    def perform_create(self, serializer):
        org = self.get_organization()
        
        # Verify Billing Entitlements limit
        from billing.models import WorkspaceSubscription, Plan
        from django.utils import timezone
        from billing.views import get_or_create_default_plans
        get_or_create_default_plans()

        subscription, created = WorkspaceSubscription.objects.get_or_create(
            organization=org,
            defaults={
                'plan': Plan.objects.filter(price=0).first() or Plan.objects.first(),
                'status': 'ACTIVE',
                'start_date': timezone.now(),
                'end_date': timezone.now() + timezone.timedelta(days=30)
            }
        )
        if subscription.status != 'ACTIVE':
            raise exceptions.ValidationError("Your subscription is inactive. Please update billing details.")

        current_projects_count = Project.objects.filter(organization=org).count()
        if current_projects_count >= subscription.plan.quota_projects:
            raise exceptions.ValidationError("Project creation limit exceeded. Please upgrade your plan.")

        project = serializer.save(organization=org)
        
        AuditLog.objects.create(
            organization=org,
            user=self.request.user,
            action="PROJECT_CREATE",
            details={"project_id": project.id, "name": project.name}
        )

    @decorators.action(detail=True, methods=['get'])
    def export_pack(self, request, org_slug=None, pk=None):
        project = self.get_object()
        assets = GeneratedAsset.objects.filter(project=project)
        
        # Build text format pack
        pack_content = f"VIRALOPS SOCIAL CONTENT PACK\n"
        pack_content += f"Project: {project.name}\n"
        pack_content += f"Exported: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        pack_content += "="*40 + "\n\n"
        
        for asset in assets:
            pack_content += f"--- {asset.get_type_display()} ({asset.get_platform_display()}) ---\n"
            pack_content += f"{asset.content}\n"
            pack_content += "\n" + "-"*40 + "\n\n"
            
        # Return as plain text download attachment
        response = HttpResponse(pack_content, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="viralops_export_{project.id}.txt"'
        return response

class SourceInputViewSet(TenantScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = SourceInput.objects.all().select_related('project', 'project__organization').order_by('-created_at')
    serializer_class = SourceInputSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrganizationMember]

    def get_throttles(self):
        if self.action == 'create':
            from rest_framework.throttling import ScopedRateThrottle
            throttle = ScopedRateThrottle()
            throttle.scope = 'ingestion'
            return [throttle]
        return super().get_throttles()


    def get_queryset(self):
        # Scoped to project
        project_id = self.kwargs.get('project_id')
        queryset = super().get_queryset()
        if project_id:
            return queryset.filter(project_id=project_id)
        return queryset

    def perform_create(self, serializer):
        project_id = self.kwargs.get('project_id')
        project = get_object_or_404(Project, id=project_id, organization=self.get_organization())
        org = project.organization

        # Verify Billing generations limit before triggering ingestion
        from billing.models import WorkspaceSubscription, Plan
        from django.utils import timezone
        from billing.views import get_or_create_default_plans
        get_or_create_default_plans()
        
        subscription, created = WorkspaceSubscription.objects.get_or_create(
            organization=org,
            defaults={
                'plan': Plan.objects.filter(price=0).first() or Plan.objects.first(),
                'status': 'ACTIVE',
                'start_date': timezone.now(),
                'end_date': timezone.now() + timezone.timedelta(days=30)
            }
        )
        if subscription.status != 'ACTIVE':
            raise exceptions.ValidationError("Your subscription is inactive. Please update billing details.")

        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_gen_count = UsageEvent.objects.filter(
            organization=org,
            event_type='AI_GENERATION',
            created_at__gte=month_start
        ).aggregate(total=models.Sum('quantity'))['total'] or 0

        if current_gen_count >= subscription.plan.quota_generations:
            raise exceptions.ValidationError("Monthly AI generation limit exceeded. Please upgrade your plan.")
        
        # Enforce file upload size validation limits locally
        uploaded_file = self.request.FILES.get('file')
        file_size = 0
        file_name = ''
        if uploaded_file:
            file_size = uploaded_file.size
            file_name = uploaded_file.name
            if file_size > 52428800:
                raise exceptions.ValidationError({"file": "File size exceeds local 50MB limits."})
        else:
            file_size_data = self.request.data.get('file_size')
            if file_size_data:
                file_size = int(file_size_data)
                if file_size > 52428800:
                    raise exceptions.ValidationError({"file_size": "File size exceeds local 50MB limits."})
            file_name = self.request.data.get('file_name', '')

        source_input = serializer.save(
            project=project, 
            status='PENDING',
            file_size=file_size if file_size else None,
            file_name=file_name if file_name else ''
        )
        
        # Log Audit
        AuditLog.objects.create(
            organization=project.organization,
            user=self.request.user,
            action="SOURCE_SUBMIT",
            details={"source_id": source_input.id, "type": source_input.type}
        )

        # Trigger Celery Ingestion Job
        process_source_input.delay(source_input.id)

    @decorators.action(detail=True, methods=['get'])
    def download(self, request, org_slug=None, project_id=None, pk=None):
        source_input = self.get_object()
        if not source_input.file:
            return Response({'error': 'No uploaded file associated with this source.'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if S3 is active by checking storage settings
        from django.core.files.storage import default_storage
        try:
            from storages.backends.s3boto3 import S3Boto3Storage
            if isinstance(default_storage, S3Boto3Storage):
                client = default_storage.connection.meta.client
                bucket = default_storage.bucket_name
                key = source_input.file.name
                
                url = client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket, 'Key': key},
                    ExpiresIn=3600
                )
                return Response({'download_url': url})
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error generating presigned S3 URL: {e}")
        
        # Local fallback pre-signed / standard URL
        url = request.build_absolute_uri(source_input.file.url)
        return Response({'download_url': url})

class GeneratedAssetViewSet(TenantScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = GeneratedAsset.objects.all().select_related('project', 'project__organization').prefetch_related('versions').order_by('-created_at')
    serializer_class = GeneratedAssetSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrganizationMember]

    def get_queryset(self):
        project_id = self.kwargs.get('project_id')
        queryset = super().get_queryset()
        if project_id:
            return queryset.filter(project_id=project_id)
        return queryset

    @decorators.action(detail=True, methods=['post'])
    def toggle_favorite(self, request, org_slug=None, pk=None, project_id=None):
        asset = self.get_object()
        asset.is_favorite = not asset.is_favorite
        asset.save()
        return Response({'is_favorite': asset.is_favorite})

    @decorators.action(detail=True, methods=['post'])
    def save_version(self, request, org_slug=None, pk=None, project_id=None):
        asset = self.get_object()
        content = request.data.get('content')
        if not content:
            return Response({'error': 'Content is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Update current content
        asset.content = content
        asset.save()
        
        # Create historical version
        version = GeneratedAssetVersion.objects.create(
            asset=asset,
            content=content,
            edited_by=request.user
        )
        
        # Log Audit
        AuditLog.objects.create(
            organization=asset.project.organization,
            user=request.user,
            action="ASSET_EDITED",
            details={"asset_id": asset.id, "version_id": version.id}
        )
        
        serializer = GeneratedAssetSerializer(asset)
        return Response(serializer.data)

    @decorators.action(detail=True, methods=['post'])
    def regenerate(self, request, org_slug=None, pk=None, project_id=None):
        asset = self.get_object()
        org = self.get_organization()
        
        # Verify Billing generations limit
        from billing.models import WorkspaceSubscription, Plan
        from django.utils import timezone
        
        subscription, created = WorkspaceSubscription.objects.get_or_create(
            organization=org,
            defaults={
                'plan': Plan.objects.filter(price=0).first() or Plan.objects.first(),
                'status': 'ACTIVE',
                'start_date': timezone.now(),
                'end_date': timezone.now() + timezone.timedelta(days=30)
            }
        )
        if subscription.status != 'ACTIVE':
            raise exceptions.ValidationError("Your subscription is inactive. Please update billing details.")

        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_gen_count = UsageEvent.objects.filter(
            organization=org,
            event_type='AI_GENERATION',
            created_at__gte=month_start
        ).aggregate(total=models.Sum('quantity'))['total'] or 0

        if current_gen_count >= subscription.plan.quota_generations:
            raise exceptions.ValidationError("Monthly AI generation limit exceeded. Please upgrade your plan.")

        # Increment usage count
        UsageEvent.objects.create(
            organization=org,
            user=request.user,
            event_type='AI_GENERATION',
            quantity=1
        )
        
        # Run asset regeneration task inline
        from .tasks import regenerate_single_asset
        regenerate_single_asset(asset.id)
        
        asset.refresh_from_db()
        serializer = GeneratedAssetSerializer(asset)
        return Response(serializer.data)

class TemplateViewSet(TenantScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Template.objects.all().order_by('-created_at')
    serializer_class = TemplateSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrganizationMember]

    def perform_create(self, serializer):
        serializer.save(organization=self.get_organization())

class MemoryRecordViewSet(TenantScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = MemoryRecord.objects.all()
    serializer_class = MemoryRecordSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrganizationMember]
    lookup_field = 'key'

    def perform_create(self, serializer):
        serializer.save(organization=self.get_organization())

class AdminOpsViewSet(viewsets.ViewSet):
    """
    Super Admin actions for monitoring queues, failed jobs, usage, and logs.
    """
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]

    @decorators.action(detail=False, methods=['get'])
    def dashboard_summary(self, request):
        total_users = User.objects.count()
        total_orgs = Organization.objects.count()
        total_projects = Project.objects.count()
        total_jobs = ProcessingJob.objects.count()
        failed_jobs = ProcessingJob.objects.filter(status='FAILED').count()
        
        # Usage aggregations
        transcription_usage = UsageEvent.objects.filter(event_type='TRANSCRIPTION_MINUTES').aggregate(total=models.Sum('quantity'))['total'] or 0
        ai_usage = UsageEvent.objects.filter(event_type='AI_GENERATION').aggregate(total=models.Sum('quantity'))['total'] or 0
        
        return Response({
            'total_users': total_users,
            'total_organizations': total_orgs,
            'total_projects': total_projects,
            'total_jobs': total_jobs,
            'failed_jobs': failed_jobs,
            'usage_transcription_minutes': transcription_usage,
            'usage_ai_generations': ai_usage
        })

    @decorators.action(detail=False, methods=['get'])
    def job_queue(self, request):
        jobs = ProcessingJob.objects.all().order_by('-created_at')[:50]
        serializer = ProcessingJobSerializer(jobs, many=True)
        return Response(serializer.data)

    @decorators.action(detail=False, methods=['get'])
    def audit_logs(self, request):
        logs = AuditLog.objects.all().order_by('-created_at')[:100]
        serializer = AuditLogSerializer(logs, many=True)
        return Response(serializer.data)

    @decorators.action(detail=True, methods=['post'])
    def retry_job(self, request, pk=None):
        job = get_object_or_404(ProcessingJob, id=pk)
        job.status = 'PENDING'
        job.error_log = ''
        job.save()
        
        # Re-trigger background task
        process_source_input.delay(job.source_input.id)
        
        return Response({'status': 'Job scheduled for retry'})
