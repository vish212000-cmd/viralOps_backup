from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core import mail
from django.core import signing
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
import os

User = get_user_model()

class EmailAuthTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('auth-register')
        self.login_url = reverse('auth-login')
        self.verify_url = reverse('auth-verify-email')
        self.resend_url = reverse('auth-resend-verification')
        self.reset_url = reverse('auth-password-reset')
        self.reset_confirm_url = reverse('auth-password-reset-confirm')
        
        # Ensure verification is enabled for testing
        os.environ['EMAIL_VERIFICATION_REQUIRED'] = 'True'

    def test_registration_sends_email_and_blocks_login(self):
        # Register User
        payload = {
            'username': 'verify_user',
            'email': 'verify@viralops.com',
            'password': 'Password123!'
        }
        res = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        
        user = User.objects.get(username='verify_user')
        self.assertFalse(user.is_email_verified)
        
        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Verify Your Email Address", mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, ['verify@viralops.com'])

        # Attempt Login (should be blocked)
        login_payload = {
            'username': 'verify_user',
            'password': 'Password123!'
        }
        login_res = self.client.post(self.login_url, login_payload, format='json')
        self.assertEqual(login_res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('verify your email address', login_res.data['detail'].lower())

    def test_verify_email_endpoint(self):
        # Create unverified user
        user = User.objects.create_user(
            username='verify_token_user',
            email='token@viralops.com',
            password='Password123!'
        )
        self.assertFalse(user.is_email_verified)
        
        # Generate token
        token = signing.dumps({'user_id': user.id}, salt='email-verify')
        
        # Post to verify endpoint
        res = self.client.post(self.verify_url, {'token': token}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        # Check user is verified
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)
        
        # Test login succeeds now
        login_payload = {
            'username': 'verify_token_user',
            'password': 'Password123!'
        }
        login_res = self.client.post(self.login_url, login_payload, format='json')
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)
        self.assertEqual(login_res.data['detail'], 'OTP sent to email.')
        
        # Get OTP from DB
        from accounts.models import EmailOTP
        otp_record = EmailOTP.objects.get(user=user, purpose='LOGIN')
        # We can't know the raw OTP since it's hashed and random, but we can bypass it by saving a known hash
        from django.contrib.auth.hashers import make_password
        otp_record.otp_hash = make_password('123456')
        otp_record.save()
        
        verify_payload = {
            'username': 'verify_token_user',
            'otp': '123456'
        }
        verify_url = reverse('auth-login-verify')
        verify_res = self.client.post(verify_url, verify_payload, format='json')
        self.assertEqual(verify_res.status_code, status.HTTP_200_OK)
        self.assertIn('access', verify_res.data)

    def test_resend_verification_email(self):
        user = User.objects.create_user(
            username='resend_user',
            email='resend@viralops.com',
            password='Password123!'
        )
        mail.outbox = [] # Clear outbox
        
        res = self.client.post(self.resend_url, {'email': 'resend@viralops.com'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)

    def test_password_reset_flow(self):
        user = User.objects.create_user(
            username='reset_user',
            email='reset@viralops.com',
            password='OldPassword123!',
            is_email_verified=True
        )
        mail.outbox = []
        
        # Request password reset
        res = self.client.post(self.reset_url, {'email': 'reset@viralops.com'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        
        # Extract token from mail
        sent_email = mail.outbox[0]
        self.assertIn("Password Reset Code", sent_email.subject)
        
        # Get OTP from DB
        from accounts.models import EmailOTP
        from django.contrib.auth.hashers import make_password
        otp_record = EmailOTP.objects.get(user=user, purpose='PASSWORD_RESET')
        otp_record.otp_hash = make_password('123456')
        otp_record.save()
        
        # Confirm password reset
        confirm_payload = {
            'email': 'reset@viralops.com',
            'otp': '123456',
            'password': 'NewPassword123!'
        }
        confirm_res = self.client.post(self.reset_confirm_url, confirm_payload, format='json')
        self.assertEqual(confirm_res.status_code, status.HTTP_200_OK)
        
        # Check login
        login_payload = {
            'username': 'reset_user',
            'password': 'NewPassword123!'
        }
        login_res = self.client.post(self.login_url, login_payload, format='json')
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)


class GoogleOAuthTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.google_auth_url = reverse('auth-google')

    def test_google_oauth_signup_new_user(self):
        payload = {
            'code': 'mock_google_code',
            'email': 'new_oauth_user@viralops.com'
        }
        res = self.client.post(self.google_auth_url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        user = User.objects.get(email='new_oauth_user@viralops.com')
        self.assertEqual(user.username, 'new_oauth_user')
        self.assertTrue(user.is_email_verified)
        
        from allauth.socialaccount.models import SocialAccount
        self.assertTrue(SocialAccount.objects.filter(user=user, provider='google').exists())
        self.assertIn('access', res.data)
        self.assertIn('refresh', res.data)

    def test_google_oauth_link_existing_user(self):
        user = User.objects.create_user(
            username='existing_user',
            email='existing_oauth@viralops.com',
            password='Password123!',
            is_email_verified=False
        )
        
        payload = {
            'code': 'mock_google_code',
            'email': 'existing_oauth@viralops.com'
        }
        res = self.client.post(self.google_auth_url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        self.assertEqual(User.objects.filter(email='existing_oauth@viralops.com').count(), 1)
        
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)
        
        from allauth.socialaccount.models import SocialAccount
        self.assertTrue(SocialAccount.objects.filter(user=user, provider='google').exists())

    def test_google_oauth_username_deduplication(self):
        User.objects.create_user(
            username='conflict_user',
            email='conflict@example.com',
            password='Password123!'
        )
        
        payload = {
            'code': 'mock_google_code',
            'email': 'conflict_user@viralops.com'
        }
        res = self.client.post(self.google_auth_url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        user = User.objects.get(email='conflict_user@viralops.com')
        self.assertNotEqual(user.username, 'conflict_user')
        self.assertTrue(user.username.startswith('conflict_user_'))

