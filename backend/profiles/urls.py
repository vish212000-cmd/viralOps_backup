from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AccountViewSet, APITokenViewSet, SessionHistoryViewSet, ConnectedAccountsViewSet

app_name = 'profiles'

router = DefaultRouter()
router.register(r'tokens', APITokenViewSet, basename='api-token')
router.register(r'sessions', SessionHistoryViewSet, basename='session-history')
router.register(r'accounts', ConnectedAccountsViewSet, basename='connected-account')

urlpatterns = [
    path('me/', AccountViewSet.as_view({'get': 'list', 'post': 'create', 'put': 'create', 'patch': 'create'}), name='account-me'),
    path('me/avatar/', AccountViewSet.as_view({'post': 'avatar', 'delete': 'avatar'}), name='account-avatar'),
    path('me/change_password/', AccountViewSet.as_view({'post': 'change_password'}), name='account-change-password'),
    path('', include(router.urls)),
]
