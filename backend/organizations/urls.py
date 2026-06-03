from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrganizationViewSet, AcceptWorkspaceInviteView

router = DefaultRouter()
router.register(r'', OrganizationViewSet, basename='organization')

urlpatterns = [
    path('accept-invite/', AcceptWorkspaceInviteView.as_view(), name='accept-invite'),
    path('', include(router.urls)),
]
