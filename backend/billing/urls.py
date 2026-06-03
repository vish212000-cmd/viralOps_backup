from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PlanViewSet, BillingStatusView, PaymentVerificationView,
    SubscriptionCancelView, BillingHistoryView, WebhookReceiverView
)

router = DefaultRouter()
router.register('plans', PlanViewSet, basename='plans')

urlpatterns = [
    # Router endpoints (e.g. /api/billing/plans/)
    path('', include(router.urls)),

    # Webhook Endpoint (e.g. /api/billing/webhook/)
    path('webhook/', WebhookReceiverView.as_view(), name='billing-webhook'),

    # Workspace-Scoped Endpoints (e.g. /api/billing/orgs/<slug>/...)
    path('orgs/<str:org_slug>/status/', BillingStatusView.as_view(), name='billing-status'),
    path('orgs/<str:org_slug>/verify-payment/', PaymentVerificationView.as_view(), name='billing-verify-payment'),
    path('orgs/<str:org_slug>/cancel/', SubscriptionCancelView.as_view(), name='billing-cancel'),
    path('orgs/<str:org_slug>/history/', BillingHistoryView.as_view(), name='billing-history'),
]
