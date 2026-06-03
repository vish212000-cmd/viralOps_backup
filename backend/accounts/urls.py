from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import UserRegisterView
from .google_auth import GoogleOAuthView

urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='auth-register'),
    path('login/', TokenObtainPairView.as_view(), name='auth-login'),
    path('refresh/', TokenRefreshView.as_view(), name='auth-refresh'),
    path('google/', GoogleOAuthView.as_view(), name='auth-google'),
]
