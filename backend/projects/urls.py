from django.urls import path
from .views import (
    ProjectViewSet, SourceInputViewSet, GeneratedAssetViewSet,
    TemplateViewSet, MemoryRecordViewSet, AdminOpsViewSet
)
from .analytics import (
    WorkspaceSummaryView, WorkspaceTrendsView,
    AdminAnalyticsSummaryView, AdminSystemHealthView
)

# Explicit router mappings for ViewSets
project_list = ProjectViewSet.as_view({
    'get': 'list',
    'post': 'create'
})
project_detail = ProjectViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})

source_list = SourceInputViewSet.as_view({
    'get': 'list',
    'post': 'create'
})
source_detail = SourceInputViewSet.as_view({
    'get': 'retrieve',
    'delete': 'destroy'
})

asset_list = GeneratedAssetViewSet.as_view({
    'get': 'list',
})
asset_detail = GeneratedAssetViewSet.as_view({
    'get': 'retrieve',
    'delete': 'destroy'
})

template_list = TemplateViewSet.as_view({
    'get': 'list',
    'post': 'create'
})
template_detail = TemplateViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'delete': 'destroy'
})

memory_list = MemoryRecordViewSet.as_view({
    'get': 'list',
    'post': 'create'
})
memory_detail = MemoryRecordViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'delete': 'destroy'
})

admin_summary = AdminOpsViewSet.as_view({
    'get': 'dashboard_summary'
})
admin_jobs = AdminOpsViewSet.as_view({
    'get': 'job_queue'
})
admin_logs = AdminOpsViewSet.as_view({
    'get': 'audit_logs'
})
admin_retry = AdminOpsViewSet.as_view({
    'post': 'retry_job'
})

urlpatterns = [
    # Projects
    path('orgs/<str:org_slug>/projects/', project_list, name='project-list'),
    path('orgs/<str:org_slug>/projects/<int:pk>/', project_detail, name='project-detail'),
    path('orgs/<str:org_slug>/projects/<int:pk>/export_pack/', ProjectViewSet.as_view({'get': 'export_pack'}), name='project-export-pack'),
    
    # Sources (scoped to project)
    path('orgs/<str:org_slug>/projects/<int:project_id>/sources/', source_list, name='source-list'),
    path('orgs/<str:org_slug>/projects/<int:project_id>/sources/<int:pk>/', source_detail, name='source-detail'),
    
    # Assets (scoped to project)
    path('orgs/<str:org_slug>/projects/<int:project_id>/assets/', asset_list, name='asset-list'),
    path('orgs/<str:org_slug>/projects/<int:project_id>/assets/<int:pk>/', asset_detail, name='asset-detail'),
    path('orgs/<str:org_slug>/projects/<int:project_id>/assets/<int:pk>/toggle_favorite/', GeneratedAssetViewSet.as_view({'post': 'toggle_favorite'}), name='asset-toggle-favorite'),
    path('orgs/<str:org_slug>/projects/<int:project_id>/assets/<int:pk>/save_version/', GeneratedAssetViewSet.as_view({'post': 'save_version'}), name='asset-save-version'),
    path('orgs/<str:org_slug>/projects/<int:project_id>/assets/<int:pk>/regenerate/', GeneratedAssetViewSet.as_view({'post': 'regenerate'}), name='asset-regenerate'),
    
    # Templates
    path('orgs/<str:org_slug>/templates/', template_list, name='template-list'),
    path('orgs/<str:org_slug>/templates/<int:pk>/', template_detail, name='template-detail'),
    
    # Memory/Preferences
    path('orgs/<str:org_slug>/memory/', memory_list, name='memory-list'),
    path('orgs/<str:org_slug>/memory/<str:key>/', memory_detail, name='memory-detail'),
    
    # Admin Panel APIs
    path('adminops/summary/', admin_summary, name='admin-summary'),
    path('adminops/jobs/', admin_jobs, name='admin-jobs'),
    path('adminops/logs/', admin_logs, name='admin-logs'),
    path('adminops/jobs/<int:pk>/retry/', admin_retry, name='admin-retry-job'),

    # Analytics
    path('analytics/orgs/<str:org_slug>/workspace/summary/', WorkspaceSummaryView.as_view(), name='analytics-workspace-summary'),
    path('analytics/orgs/<str:org_slug>/workspace/trends/', WorkspaceTrendsView.as_view(), name='analytics-workspace-trends'),
    path('analytics/admin/summary/', AdminAnalyticsSummaryView.as_view(), name='analytics-admin-summary'),
    path('analytics/admin/system-health/', AdminSystemHealthView.as_view(), name='analytics-admin-system-health'),
]
