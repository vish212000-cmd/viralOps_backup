from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlanViewSet, MySubscriptionViewSet, WebhookViewSet

router = DefaultRouter()
router.register(r'plans', PlanViewSet, basename='plan')
router.register(r'subscription', MySubscriptionViewSet, basename='subscription')

urlpatterns = [
    path('webhook/', WebhookViewSet.as_view(), name='razorpay-webhook'),
    path('', include(router.urls)),
]
