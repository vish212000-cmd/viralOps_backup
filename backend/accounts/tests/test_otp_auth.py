from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from accounts.models import EmailOTP
from django.utils import timezone
from datetime import timedelta
import os
from unittest.mock import patch
from django.contrib.auth.hashers import make_password

User = get_user_model()

class OTPAuthTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpassword123')
        self.user.is_email_verified = True
        self.user.save()
        self.login_initiate_url = reverse('auth-login')
        self.login_verify_url = reverse('auth-login-verify')
        self.password_reset_url = reverse('auth-password-reset')
        self.password_reset_confirm_url = reverse('auth-password-reset-confirm')

    @patch('accounts.views.send_mail')
    def test_login_initiate_success(self, mock_send_mail):
        response = self.client.post(self.login_initiate_url, {
            'username': 'testuser',
            'password': 'testpassword123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], 'OTP sent to email.')
        self.assertTrue(EmailOTP.objects.filter(user=self.user, purpose='LOGIN').exists())
        self.assertTrue(mock_send_mail.called)

    def test_login_initiate_invalid_credentials(self):
        response = self.client.post(self.login_initiate_url, {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_verify_otp_success(self):
        # Create OTP
        raw_otp = "123456"
        EmailOTP.objects.create(
            user=self.user,
            otp_hash=make_password(raw_otp),
            purpose='LOGIN',
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        
        response = self.client.post(self.login_verify_url, {
            'username': 'testuser',
            'otp': raw_otp
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        
        # Verify OTP is marked as used
        otp_record = EmailOTP.objects.get(user=self.user, purpose='LOGIN')
        self.assertTrue(otp_record.is_used)

    def test_login_verify_otp_invalid(self):
        EmailOTP.objects.create(
            user=self.user,
            otp_hash=make_password("123456"),
            purpose='LOGIN',
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        
        response = self.client.post(self.login_verify_url, {
            'username': 'testuser',
            'otp': "654321"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_verify_otp_expired(self):
        EmailOTP.objects.create(
            user=self.user,
            otp_hash=make_password("123456"),
            purpose='LOGIN',
            expires_at=timezone.now() - timedelta(minutes=1)
        )
        
        response = self.client.post(self.login_verify_url, {
            'username': 'testuser',
            'otp': "123456"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rate_limiting_otp_sends(self):
        # Create 3 recent OTPs
        for _ in range(3):
            EmailOTP.objects.create(
                user=self.user,
                otp_hash="hash",
                purpose='LOGIN',
                expires_at=timezone.now() + timedelta(minutes=10)
            )
            
        response = self.client.post(self.login_initiate_url, {
            'username': 'testuser',
            'password': 'testpassword123'
        })
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    @patch('accounts.views.send_mail')
    def test_password_reset_flow(self, mock_send_mail):
        # 1. Request Reset
        response = self.client.post(self.password_reset_url, {
            'email': 'test@example.com'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(EmailOTP.objects.filter(user=self.user, purpose='PASSWORD_RESET').exists())
        
        # We don't know the raw OTP because it's mocked, so let's mock it in DB for step 2
        otp_record = EmailOTP.objects.filter(user=self.user, purpose='PASSWORD_RESET').first()
        raw_otp = "123456"
        otp_record.otp_hash = make_password(raw_otp)
        otp_record.save()
        
        # 2. Confirm Reset
        response2 = self.client.post(self.password_reset_confirm_url, {
            'email': 'test@example.com',
            'otp': raw_otp,
            'password': 'newpassword123'
        })
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Verify password changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123'))
