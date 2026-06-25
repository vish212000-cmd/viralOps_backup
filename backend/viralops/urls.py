from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

import os

def trigger_error(request):
    division_by_zero = 1 / 0

from projects.health import HealthzView, ReadyView

urlpatterns = [
    path('healthz/', HealthzView.as_view(), name='root-healthz'),
    path('ready/', ReadyView.as_view(), name='root-ready'),
    path(os.getenv('ADMIN_PATH', 'admin/'), admin.site.urls),
    path('sentry-debug/', trigger_error),
    path('prometheus/', include('django_prometheus.urls')),
    path('api/auth/', include('accounts.urls')),
    path('api/workspaces/', include('organizations.urls')),
    path('api/', include('projects.urls')),
    path('api/billing/', include('billing.urls')),
    path('api/profiles/', include('profiles.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
