import os
import logging
from django.core import signing
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status, views, permissions
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    UserRegisterSerializer, LoginInitiateSerializer, LoginVerifyOTPSerializer,
    PasswordResetRequestOTPSerializer, PasswordResetConfirmOTPSerializer
)
import random
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import authenticate
from .models import EmailOTP

logger = logging.getLogger(__name__)
User = get_user_model()

def send_verification_email(user):
    token = signing.dumps({'user_id': user.id}, salt='email-verify')
    frontend_url = os.getenv('FRONTEND_URL')
    if not frontend_url:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured("FRONTEND_URL environment variable is not set.")
    verification_url = f"{frontend_url.rstrip('/')}/verify-email?token={token}"
    
    context = {'user': user, 'verification_url': verification_url}
    html_content = render_to_string('accounts/emails/verification_email.html', context)
    text_content = render_to_string('accounts/emails/verification_email.txt', context)
    
    send_mail(
        subject="Verify Your Email Address - ViralOps",
        message=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_content,
        fail_silently=False
    )

def generate_otp_for_user(user, purpose):
    now = timezone.now()
    fifteen_mins_ago = now - timedelta(minutes=15)
    recent_otps = EmailOTP.objects.filter(user=user, created_at__gte=fifteen_mins_ago).count()
    if recent_otps >= 3:
        raise Exception("Too many OTP requests. Please wait 15 minutes.")
    
    raw_otp = f"{random.randint(0, 999999):06d}"
    otp_hash = make_password(raw_otp)
    expires_at = now + timedelta(minutes=10)
    
    EmailOTP.objects.create(
        user=user,
        otp_hash=otp_hash,
        purpose=purpose,
        expires_at=expires_at
    )
    return raw_otp

def send_otp_email(user, raw_otp, purpose):
    if purpose == 'LOGIN':
        subject = "Your Login Verification Code - ViralOps"
        text_content = f"Your verification code is: {raw_otp}\nIt expires in 10 minutes."
    else:
        subject = "Password Reset Code - ViralOps"
        text_content = f"Your password reset code is: {raw_otp}\nIt expires in 10 minutes."
    
    send_mail(
        subject=subject,
        message=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False
    )

def send_invite_email(invite):
    frontend_url = os.getenv('FRONTEND_URL')
    if not frontend_url:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured("FRONTEND_URL environment variable is not set.")
    invite_url = f"{frontend_url.rstrip('/')}/accept-invite?token={invite.id}"
    
    invited_by_name = invite.invited_by.username if invite.invited_by else 'An administrator'
    context = {
        'organization': invite.organization,
        'role': invite.role,
        'invited_by_name': invited_by_name,
        'invite_url': invite_url
    }
    html_content = render_to_string('accounts/emails/invite_email.html', context)
    text_content = render_to_string('accounts/emails/invite_email.txt', context)
    
    send_mail(
        subject=f"Invitation to join {invite.organization.name} workspace on ViralOps",
        message=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[invite.email],
        html_message=html_content,
        fail_silently=False
    )

class UserRegisterView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            try:
                send_verification_email(user)
            except Exception as e:
                logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
            
            return Response({
                'user': {
                    'username': user.username,
                    'email': user.email,
                },
                'message': 'Registration successful. Please verify your email to log in.'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginInitiateView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginInitiateSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = authenticate(username=username, password=password)
            if not user:
                return Response({'detail': 'Invalid username or password.'}, status=status.HTTP_401_UNAUTHORIZED)

            if getattr(settings, 'EMAIL_VERIFICATION_REQUIRED', False) and not getattr(user, 'is_email_verified', True):
                return Response({'detail': 'Please verify your email address before logging in.'}, status=status.HTTP_401_UNAUTHORIZED)

            # --- TOTP MFA path ---
            if user.is_mfa_enabled:
                mfa_token = serializer.validated_data.get('mfa_token', '').strip()
                if not mfa_token:
                    return Response({'mfa_required': True}, status=status.HTTP_400_BAD_REQUEST)
                from accounts.totp import verify_totp_code
                if not verify_totp_code(user.mfa_secret, mfa_token):
                    return Response(
                        {'detail': 'Invalid Multi-Factor Authentication code.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                # TOTP verified — issue JWT immediately
                refresh = RefreshToken.for_user(user)
                return Response({
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }, status=status.HTTP_200_OK)

            # --- Email OTP path (MFA not enabled) ---
            try:
                raw_otp = generate_otp_for_user(user, 'LOGIN')
                send_otp_email(user, raw_otp, 'LOGIN')
                return Response({'detail': 'OTP sent to email.', 'email': user.email}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'detail': str(e)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginVerifyOTPView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginVerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            raw_otp = serializer.validated_data['otp']
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
            
            if user.is_mfa_enabled:
                return Response({'detail': 'This account requires Authenticator MFA. Email OTP login is disabled.'}, status=status.HTTP_403_FORBIDDEN)
                
            
            now = timezone.now()
            otp_record = EmailOTP.objects.filter(
                user=user, purpose='LOGIN', is_used=False, expires_at__gt=now
            ).order_by('-created_at').first()

            if not otp_record:
                return Response({'detail': 'No active OTP found or OTP has expired.'}, status=status.HTTP_400_BAD_REQUEST)
            
            if otp_record.attempts >= 5:
                return Response({'detail': 'Maximum verification attempts exceeded. Please request a new OTP.'}, status=status.HTTP_400_BAD_REQUEST)

            otp_record.attempts += 1
            otp_record.save()

            if not check_password(raw_otp, otp_record.otp_hash):
                return Response({'detail': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)
            
            otp_record.is_used = True
            otp_record.save()

            refresh = RefreshToken.for_user(user)
            return Response({
                'user': {
                    'username': user.username,
                    'email': user.email,
                },
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyEmailView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({'error': 'Token is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Unsign with 24 hours expiry
            data = signing.loads(token, salt='email-verify', max_age=86400)
            user_id = data['user_id']
            user = User.objects.get(id=user_id)
            if not user.is_email_verified:
                user.is_email_verified = True
                user.save()
            return Response({'message': 'Email address verified successfully.'}, status=status.HTTP_200_OK)
        except signing.SignatureExpired:
            return Response({'error': 'Verification token has expired.'}, status=status.HTTP_400_BAD_REQUEST)
        except (signing.BadSignature, User.DoesNotExist):
            return Response({'error': 'Invalid verification token.'}, status=status.HTTP_400_BAD_REQUEST)

class ResendVerificationEmailView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            if user.is_email_verified:
                return Response({'message': 'Email is already verified.'}, status=status.HTTP_200_OK)
            
            send_verification_email(user)
            return Response({'message': 'Verification email resent successfully.'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            # Mask existence of emails to prevent enumeration
            return Response({'message': 'Verification email resent successfully.'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error resending verification: {str(e)}")
            return Response({'error': 'Failed to resend verification email.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PasswordResetRequestView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                raw_otp = generate_otp_for_user(user, 'PASSWORD_RESET')
                send_otp_email(user, raw_otp, 'PASSWORD_RESET')
            except User.DoesNotExist:
                pass # Mask user existence
            except Exception as e:
                logger.error(f"Error requesting password reset: {str(e)}")
                return Response({'error': str(e)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
                
            return Response({'message': 'If an account exists with this email, an OTP has been sent.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetConfirmView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            raw_otp = serializer.validated_data['otp']
            new_password = serializer.validated_data['password']
            
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({'error': 'Invalid request.'}, status=status.HTTP_400_BAD_REQUEST)

            now = timezone.now()
            otp_record = EmailOTP.objects.filter(
                user=user, purpose='PASSWORD_RESET', is_used=False, expires_at__gt=now
            ).order_by('-created_at').first()

            if not otp_record:
                return Response({'error': 'No active OTP found or OTP has expired.'}, status=status.HTTP_400_BAD_REQUEST)
            
            if otp_record.attempts >= 5:
                return Response({'error': 'Maximum verification attempts exceeded. Please request a new OTP.'}, status=status.HTTP_400_BAD_REQUEST)

            otp_record.attempts += 1
            otp_record.save()

            if not check_password(raw_otp, otp_record.otp_hash):
                return Response({'error': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)
            
            otp_record.is_used = True
            otp_record.save()

            user.set_password(new_password)
            user.save()
            return Response({'message': 'Password has been reset successfully.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EnableMFAView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.is_mfa_enabled:
            return Response({'detail': 'MFA is already enabled.'}, status=status.HTTP_400_BAD_REQUEST)
        
        from accounts.totp import generate_secret, get_provisioning_uri
        if not user.mfa_secret:
            user.mfa_secret = generate_secret()
            user.save()
            
        uri = get_provisioning_uri(user.mfa_secret, user.email)
        return Response({
            'secret': user.mfa_secret,
            'provisioning_uri': uri
        }, status=status.HTTP_200_OK)

class VerifyMFAView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.is_mfa_enabled:
            return Response({'detail': 'MFA is already enabled.'}, status=status.HTTP_400_BAD_REQUEST)
            
        code = request.data.get('code')
        if not code:
            return Response({'error': 'Verification code is required.'}, status=status.HTTP_400_BAD_REQUEST)
            
        from accounts.totp import verify_totp_code
        if verify_totp_code(user.mfa_secret, code):
            user.is_mfa_enabled = True
            user.save()
            return Response({'detail': 'MFA has been successfully verified and enabled.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid verification code.'}, status=status.HTTP_400_BAD_REQUEST)

class DisableMFAView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        if not user.is_mfa_enabled:
            return Response({'detail': 'MFA is already disabled.'}, status=status.HTTP_400_BAD_REQUEST)
            
        code = request.data.get('code')
        if not code:
            return Response({'error': 'Verification code is required to disable MFA.'}, status=status.HTTP_400_BAD_REQUEST)
            
        from accounts.totp import verify_totp_code
        if verify_totp_code(user.mfa_secret, code):
            user.is_mfa_enabled = False
            user.mfa_secret = ''
            user.save()
            return Response({'detail': 'MFA has been successfully disabled.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid verification code.'}, status=status.HTTP_400_BAD_REQUEST)


from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.response import Response

class SMTPHealthCheckView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        from django.core.mail import get_connection
        try:
            connection = get_connection()
            connection.open()
            connection.close()
            return Response({'status': 'healthy', 'message': 'SMTP connection successful'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'status': 'unhealthy', 'message': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

