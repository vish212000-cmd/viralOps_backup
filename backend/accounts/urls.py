from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserRegisterView, LoginInitiateView, LoginVerifyOTPView, VerifyEmailView,
    ResendVerificationEmailView, PasswordResetRequestView, PasswordResetConfirmView,
    EnableMFAView, VerifyMFAView, DisableMFAView, SMTPHealthCheckView
)
from .google_auth import GoogleOAuthView

urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='auth-register'),
    path('login/', LoginInitiateView.as_view(), name='auth-login'),
    path('login/verify/', LoginVerifyOTPView.as_view(), name='auth-login-verify'),
    path('refresh/', TokenRefreshView.as_view(), name='auth-refresh'),
    path('google/', GoogleOAuthView.as_view(), name='auth-google'),
    path('verify-email/', VerifyEmailView.as_view(), name='auth-verify-email'),
    path('resend-verification/', ResendVerificationEmailView.as_view(), name='auth-resend-verification'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='auth-password-reset'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='auth-password-reset-confirm'),
    path('mfa/enable/', EnableMFAView.as_view(), name='auth-mfa-enable'),
    path('mfa/verify/', VerifyMFAView.as_view(), name='auth-mfa-verify'),
    path('mfa/disable/', DisableMFAView.as_view(), name='auth-mfa-disable'),
    path('smtp-health/', SMTPHealthCheckView.as_view(), name='auth-smtp-health'),
]
