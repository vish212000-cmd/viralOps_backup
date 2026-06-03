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
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .serializers import UserRegisterSerializer

logger = logging.getLogger(__name__)
User = get_user_model()

def send_verification_email(user):
    token = signing.dumps({'user_id': user.id}, salt='email-verify')
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
    verification_url = f"{frontend_url}/verify-email?token={token}"
    
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

def send_password_reset_email(user):
    token = signing.dumps({'user_id': user.id}, salt='password-reset')
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
    reset_url = f"{frontend_url}/reset-password?token={token}"
    
    context = {'user': user, 'reset_url': reset_url}
    html_content = render_to_string('accounts/emails/password_reset_email.html', context)
    text_content = render_to_string('accounts/emails/password_reset_email.txt', context)
    
    send_mail(
        subject="Reset Your Password - ViralOps",
        message=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_content,
        fail_silently=False
    )

def send_invite_email(invite):
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
    invite_url = f"{frontend_url}/accept-invite?token={invite.id}"
    
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
            
            # Note: We still return tokens on register for immediate sandbox onboarding convenience,
            # but any future password logins will enforce the verification gate.
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': {
                    'username': user.username,
                    'email': user.email,
                },
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Enforce email verification gate if not bypassed
        if not self.user.is_email_verified and os.getenv('EMAIL_VERIFICATION_REQUIRED', 'True') == 'True':
            raise AuthenticationFailed(
                detail='Email address is not verified. Please verify your email before logging in.',
                code='email_not_verified'
            )
        return data

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

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
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            send_password_reset_email(user)
        except User.DoesNotExist:
            pass # Mask user existence
        except Exception as e:
            logger.error(f"Error requesting password reset: {str(e)}")
            return Response({'error': 'Failed to process password reset request.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        return Response({'message': 'If an account exists with this email, a reset link has been sent.'}, status=status.HTTP_200_OK)

class PasswordResetConfirmView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = request.data.get('token')
        new_password = request.data.get('password')
        if not token or not new_password:
            return Response({'error': 'Token and password are required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 1 hour expiry
            data = signing.loads(token, salt='password-reset', max_age=3600)
            user_id = data['user_id']
            user = User.objects.get(id=user_id)
            user.set_password(new_password)
            user.save()
            return Response({'message': 'Password has been reset successfully.'}, status=status.HTTP_200_OK)
        except signing.SignatureExpired:
            return Response({'error': 'Password reset token has expired.'}, status=status.HTTP_400_BAD_REQUEST)
        except (signing.BadSignature, User.DoesNotExist):
            return Response({'error': 'Invalid password reset token.'}, status=status.HTTP_400_BAD_REQUEST)
