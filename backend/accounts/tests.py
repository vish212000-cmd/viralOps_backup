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
        self.assertIn('verified', login_res.data['detail'])

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
        self.assertIn('access', login_res.data)

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
        self.assertIn("Reset Your Password", sent_email.subject)
        
        # Generate reset token
        token = signing.dumps({'user_id': user.id}, salt='password-reset')
        
        # Confirm password reset
        confirm_payload = {
            'token': token,
            'password': 'NewPassword123!'
        }
        confirm_res = self.client.post(self.reset_confirm_url, confirm_payload, format='json')
        self.assertEqual(confirm_res.status_code, status.HTTP_200_OK)
        

        
        login_payload = {
            'username': 'reset_user',
            'password': 'NewPassword123!'
        }
        login_res = self.client.post(self.login_url, login_payload, format='json')
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)
