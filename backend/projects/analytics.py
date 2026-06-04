import logging
from django.utils import timezone
from django.db import models, connection
from django.core.cache import cache
from rest_framework import views, permissions, status
from rest_framework.response import Response

from organizations.mixins import TenantScopedQuerysetMixin
from organizations.permissions import IsOrganizationMember
from organizations.models import Organization
from projects.models import Project, SourceInput, GeneratedAsset, ProcessingJob, UsageEvent, AuditLog
from billing.models import Subscription, SubscriptionPlan, PaymentTransaction

logger = logging.getLogger(__name__)

class WorkspaceSummaryView(TenantScopedQuerysetMixin, views.APIView):
    permission_classes = [permissions.IsAuthenticated, IsOrganizationMember]

    def get(self, request, org_slug=None):
        org = self.get_organization()
        
        # Current month start
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Generations usage
        gen_usage = UsageEvent.objects.filter(
            organization=org,
            event_type='AI_GENERATION',
            created_at__gte=month_start
        ).aggregate(total=models.Sum('quantity'))['total'] or 0

        # Project count
        project_count = Project.objects.filter(organization=org).count()
        
        # Sources count
        sources_count = SourceInput.objects.filter(project__organization=org).count()
        
        # Generated assets count
        assets_count = GeneratedAsset.objects.filter(project__organization=org).count()

        # Subscription & limits
        subscription = Subscription.objects.filter(tenant=org).first()
        if subscription:
            plan_name = subscription.plan.name
            limit_projects = subscription.plan.max_projects
            limit_generations = subscription.plan.max_generations_per_month
        else:
            plan_name = 'Free Trial'
            limit_projects = 3
            limit_generations = 10

        # Processing Jobs Success Rate & Average Processing Time
        jobs = ProcessingJob.objects.filter(project__organization=org)
        total_jobs = jobs.count()
        completed_jobs = jobs.filter(status='COMPLETED')
        completed_jobs_count = completed_jobs.count()
        
        success_rate = (completed_jobs_count / total_jobs * 100) if total_jobs > 0 else 100.0

        # Average processing time (in seconds)
        # Calculate in Python to ensure cross-database compatibility (sqlite vs mysql)
        durations = []
        for job in completed_jobs:
            if job.updated_at and job.created_at:
                durations.append((job.updated_at - job.created_at).total_seconds())
        avg_processing_time = (sum(durations) / len(durations)) if durations else 0.0

        return Response({
            'plan_name': plan_name,
            'generations_count': gen_usage,
            'projects_count': project_count,
            'sources_count': sources_count,
            'assets_count': assets_count,
            'limits': {
                'limit_projects': limit_projects,
                'limit_generations': limit_generations,
            },
            'jobs_success_rate': round(success_rate, 2),
            'avg_processing_time': round(avg_processing_time, 1)
        }, status=status.HTTP_200_OK)


class WorkspaceTrendsView(TenantScopedQuerysetMixin, views.APIView):
    permission_classes = [permissions.IsAuthenticated, IsOrganizationMember]

    def get(self, request, org_slug=None):
        org = self.get_organization()
        
        # Last 30 days
        now = timezone.now()
        dates_list = [(now - timezone.timedelta(days=i)).date() for i in range(29, -1, -1)]
        
        # Fetch generation events
        start_date = timezone.make_aware(timezone.datetime.combine(dates_list[0], timezone.datetime.min.time()))
        gen_events = UsageEvent.objects.filter(
            organization=org,
            event_type='AI_GENERATION',
            created_at__gte=start_date
        )
        
        # Fetch project creations
        projects = Project.objects.filter(
            organization=org,
            created_at__gte=start_date
        )

        # Map to date dictionaries
        gen_by_date = {}
        for event in gen_events:
            d = event.created_at.date()
            gen_by_date[d] = gen_by_date.get(d, 0) + event.quantity
            
        proj_by_date = {}
        for p in projects:
            d = p.created_at.date()
            proj_by_date[d] = proj_by_date.get(d, 0) + 1

        dates_str = []
        generations_data = []
        projects_data = []

        for d in dates_list:
            dates_str.append(d.strftime('%b %d'))
            generations_data.append(gen_by_date.get(d, 0))
            projects_data.append(proj_by_date.get(d, 0))

        return Response({
            'dates': dates_str,
            'generations': generations_data,
            'projects': projects_data
        }, status=status.HTTP_200_OK)


class AdminAnalyticsSummaryView(views.APIView):
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def get(self, request):
        active_workspaces = Organization.objects.count()
        
        # Revenue
        total_revenue = PaymentTransaction.objects.filter(status='CAPTURED').aggregate(total=models.Sum('amount'))['total'] or 0.00
        
        # Job counts
        job_counts = ProcessingJob.objects.values('status').annotate(count=models.Count('id'))
        job_status_counts = {
            'PENDING': 0,
            'RUNNING': 0,
            'COMPLETED': 0,
            'FAILED': 0
        }
        for item in job_counts:
            job_status_counts[item['status']] = item['count']

        # Plan Breakdown
        plan_counts = WorkspaceSubscription.objects.values('plan__name').annotate(count=models.Count('id'))
        plan_breakdown = {item['plan__name']: item['count'] for item in plan_counts}
        
        # Make sure default Free Trial / Pro are listed
        if 'Free Trial' not in plan_breakdown:
            plan_breakdown['Free Trial'] = 0
        if 'Creator Pro' not in plan_breakdown:
            plan_breakdown['Creator Pro'] = 0
        if 'Enterprise' not in plan_breakdown:
            plan_breakdown['Enterprise'] = 0

        return Response({
            'active_workspaces': active_workspaces,
            'total_revenue': float(total_revenue),
            'job_status_counts': job_status_counts,
            'plan_breakdown': plan_breakdown
        }, status=status.HTTP_200_OK)


class AdminSystemHealthView(views.APIView):
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def get(self, request):
        # Database connectivity status
        db_alive = True
        try:
            connection.ensure_connection()
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            db_alive = False

        # Redis / Cache connectivity status
        redis_alive = True
        try:
            cache.set('health_check', 'ok', 5)
            if cache.get('health_check') != 'ok':
                redis_alive = False
        except Exception as e:
            logger.error(f"Cache/Redis health check failed: {e}")
            redis_alive = False

        # Queue active/pending jobs count
        active_jobs = ProcessingJob.objects.filter(status__in=['PENDING', 'RUNNING']).count()
        
        # Recent processing failures
        recent_failures_count = ProcessingJob.objects.filter(
            status='FAILED',
            updated_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).count()

        # Compile detailed system health check status
        health_status = 'HEALTHY' if db_alive and redis_alive and active_jobs < 50 else 'DEGRADED'

        return Response({
            'status': health_status,
            'services': {
                'database': 'UP' if db_alive else 'DOWN',
                'cache_redis': 'UP' if redis_alive else 'DOWN',
            },
            'queue': {
                'active_jobs_count': active_jobs,
                'failed_jobs_last_7_days': recent_failures_count
            },
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
