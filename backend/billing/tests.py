import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from organizations.models import Organization, Membership
from billing.models import SubscriptionPlan, Subscription, Invoice, PaymentTransaction
from billing.services.razorpay_service import RazorpayService
from billing.views import get_or_create_default_plans

User = get_user_model()

class BillingTests(APITestCase):
    def setUp(self):
        get_or_create_default_plans()
        self.user1 = User.objects.create_user(username='user1', email='user1@viralops.com', password='password123', is_email_verified=True)
        self.org1 = Organization.objects.create(name='Org 1', slug='org-1')
        self.membership1 = Membership.objects.create(user=self.user1, organization=self.org1, role='ADMIN')

        self.user2 = User.objects.create_user(username='user2', email='user2@viralops.com', password='password123', is_email_verified=True)
        self.org2 = Organization.objects.create(name='Org 2', slug='org-2')
        self.membership2 = Membership.objects.create(user=self.user2, organization=self.org2, role='ADMIN')

        self.client.force_authenticate(user=self.user1)
        self.free_plan = SubscriptionPlan.objects.get(name='FREE')
        self.pro_plan = SubscriptionPlan.objects.get(name='PRO')

    def test_razorpay_service_create_order(self):
        svc = RazorpayService()
        order = svc.create_order(10000, 'INR', 'cust_123', {'notes': 'test'})
        self.assertIn('id', order)
        self.assertEqual(order['amount'], 10000)

    def test_create_upgrade_order(self):
        url = reverse('subscription-list')  # POST /api/billing/subscription/
        self.client.credentials(HTTP_X_ORG_SLUG=self.org1.slug)
        res = self.client.post(url, {'plan_id': self.pro_plan.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('order_id', res.data)

    def test_payment_verification_and_activation(self):
        url = reverse('subscription-verify')  # POST /api/billing/subscription/verify/
        self.client.credentials(HTTP_X_ORG_SLUG=self.org1.slug)
        
        # Verify payment signature
        res = self.client.post(url, {
            'order_id': 'order_123',
            'payment_id': 'pay_123',
            'signature': 'mock_signature',
            'plan_id': self.pro_plan.id
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        # Verify subscription is activated
        sub = Subscription.objects.get(tenant=self.org1)
        self.assertEqual(sub.status, 'ACTIVE')
        self.assertEqual(sub.plan, self.pro_plan)
        self.assertTrue(Invoice.objects.filter(subscription=sub).exists())
        self.assertTrue(PaymentTransaction.objects.filter(subscription=sub).exists())

    def test_subscription_cancellation(self):
        # Create active subscription first
        sub = Subscription.objects.create(
            tenant=self.org1,
            user=self.user1,
            plan=self.pro_plan,
            status='ACTIVE'
        )
        url = reverse('subscription-cancel')  # POST /api/billing/subscription/cancel/
        self.client.credentials(HTTP_X_ORG_SLUG=self.org1.slug)
        res = self.client.post(url, {'reason': 'Too expensive'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        sub.refresh_from_db()
        self.assertEqual(sub.status, 'CANCELLED')
        self.assertEqual(sub.cancel_reason, 'Too expensive')

    def test_multi_tenant_isolation(self):
        # Create active subscription for org1
        sub1 = Subscription.objects.create(
            tenant=self.org1,
            user=self.user1,
            plan=self.pro_plan,
            status='ACTIVE'
        )
        # Create active subscription for org2
        sub2 = Subscription.objects.create(
            tenant=self.org2,
            user=self.user2,
            plan=self.free_plan,
            status='ACTIVE'
        )

        # Authenticate user1, try to access org2's billing subscription status
        self.client.force_authenticate(user=self.user1)
        self.client.credentials(HTTP_X_ORG_SLUG=self.org2.slug)
        
        url = reverse('subscription-list')
        res = self.client.get(url)
        # Should raise permission denied (403) because user1 is not a member of org2
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_webhook_event_handling(self):
        sub = Subscription.objects.create(
            tenant=self.org1,
            user=self.user1,
            plan=self.pro_plan,
            razorpay_subscription_id='sub_123',
            status='PENDING'
        )
        url = reverse('razorpay-webhook')
        payload = {
            'event': 'subscription.activated',
            'payload': {
                'subscription': {
                    'entity': {
                        'id': 'sub_123'
                    }
                }
            }
        }
        res = self.client.post(
            url, 
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_RAZORPAY_SIGNATURE='mock_webhook_signature'
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        sub.refresh_from_db()
        self.assertEqual(sub.status, 'ACTIVE')
