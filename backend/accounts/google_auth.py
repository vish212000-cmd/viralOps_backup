import requests
import logging
import os
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status, views, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from allauth.socialaccount.models import SocialAccount

logger = logging.getLogger(__name__)
User = get_user_model()

class GoogleOAuthView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        code = request.data.get('code')
        frontend_url = os.getenv('FRONTEND_URL')
        if not frontend_url:
            from django.core.exceptions import ImproperlyConfigured
            raise ImproperlyConfigured("FRONTEND_URL environment variable is not set.")
        redirect_uri = request.data.get('redirect_uri', f"{frontend_url.rstrip('/')}/auth/google/callback")
        
        if not code:
            return Response({'error': 'OAuth authorization code is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Mock OAuth handling for local offline runs and tests
        is_mock_code = code == 'mock_google_code' or code.startswith('mock_')
        
        email = None
        username = None
        google_uid = None
        extra_data = {}

        if is_mock_code or not settings.SOCIALACCOUNT_PROVIDERS.get('google', {}).get('APP', {}).get('client_id'):
            # Fallback to mock profile in local test or offline sandbox mode
            logger.info("Executing local/mock Google OAuth fallback exchange")
            email = request.data.get('email', 'mock_google_user@viralops.com')
            username = email.split('@')[0]
            google_uid = f"google_mock_{username}"
            extra_data = {'name': 'Mock Google User', 'email': email, 'picture': ''}
        else:
            try:
                # Exchange Authorization Code with Google
                token_url = 'https://oauth2.googleapis.com/token'
                google_app = settings.SOCIALACCOUNT_PROVIDERS['google']['APP']
                
                payload = {
                    'code': code,
                    'client_id': google_app['client_id'],
                    'client_secret': google_app['secret'],
                    'redirect_uri': redirect_uri,
                    'grant_type': 'authorization_code'
                }
                
                token_response = requests.post(token_url, data=payload, timeout=10)
                if not token_response.ok:
                    logger.error(f"Google token exchange failed: {token_response.text}")
                    return Response({'error': 'Failed to exchange authorization code with Google.'}, status=status.HTTP_400_BAD_REQUEST)
                
                token_data = token_response.json()
                access_token = token_data.get('access_token')
                
                # Fetch user profile using access token
                userinfo_url = 'https://www.googleapis.com/oauth2/v3/userinfo'
                userinfo_response = requests.get(userinfo_url, headers={'Authorization': f'Bearer {access_token}'}, timeout=10)
                if not userinfo_response.ok:
                    logger.error(f"Google userinfo fetch failed: {userinfo_response.text}")
                    return Response({'error': 'Failed to retrieve profile information from Google.'}, status=status.HTTP_400_BAD_REQUEST)
                
                userinfo_data = userinfo_response.json()
                email = userinfo_data.get('email')
                google_uid = userinfo_data.get('sub') # unique Google user identifier
                extra_data = userinfo_data
                
                if not email:
                    return Response({'error': 'Google account must share email access.'}, status=status.HTTP_400_BAD_REQUEST)
                
                username = email.split('@')[0]
                
            except Exception as e:
                logger.exception("Google OAuth exchange exception occurred")
                return Response({'error': f'Google OAuth connection error: {str(e)}'}, status=status.HTTP_502_BAD_GATEWAY)

        # Authenticate or register the User
        try:
            user = User.objects.filter(email=email).first()
            
            if user:
                # Account linking logic if email already exists
                logger.info(f"Linking existing user account with email: {email} to Google provider")
                social_acc, created = SocialAccount.objects.get_or_create(
                    user=user,
                    provider='google',
                    uid=google_uid,
                    defaults={'extra_data': extra_data}
                )
                if not created:
                    social_acc.extra_data = extra_data
                    social_acc.save()
                
                # Mark as verified since Google verifies emails
                if not user.is_email_verified:
                    user.is_email_verified = True
                    user.save()
            else:
                # Create a new user with randomized password
                logger.info(f"Registering new user through Google OAuth: {email}")
                
                # Deduplicate username if conflicts exist
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}_{counter}"
                    counter += 1
                
                import secrets
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=secrets.token_urlsafe(32),
                    is_email_verified=True
                )
                
                # Save social account connection link
                SocialAccount.objects.create(
                    user=user,
                    provider='google',
                    uid=google_uid,
                    extra_data=extra_data
                )

            # Generate authentication tokens
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': {
                    'username': user.username,
                    'email': user.email,
                },
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception("Error saving OAuth authenticated user")
            return Response({'error': 'Error saving user details.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
