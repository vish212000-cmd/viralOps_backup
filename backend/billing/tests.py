import json
import hmac
import hashlib
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from organizations.models import Organization, Membership
from projects.models import Project, UsageEvent
from billing.models import Plan, WorkspaceSubscription, PaymentRecord, InvoiceRecord, WebhookEventLog
from billing.views import get_or_create_default_plans

User = get_user_model()

class BillingTests(APITestCase):
    def setUp(self):
        get_or_create_default_plans()
        self.user = User.objects.create_user(username='testcreator', email='test@viralops.com', password='Password123')
        self.org = Organization.objects.create(name='Test Agency', slug='test-agency')
        self.membership = Membership.objects.create(user=self.user, organization=self.org, role='ADMIN')
        
        self.client.force_authenticate(user=self.user)
        self.free_plan = Plan.objects.get(name='Free Trial')
        self.pro_plan = Plan.objects.get(name='Creator Pro')

    def test_plan_seeding(self):
        plans_count = Plan.objects.count()
        self.assertGreaterEqual(plans_count, 3)
        self.assertTrue(Plan.objects.filter(name='Free Trial').exists())
        self.assertTrue(Plan.objects.filter(name='Creator Pro').exists())

    def test_billing_status_retrieval(self):
        url = f'/api/billing/orgs/{self.org.slug}/status/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['subscription']['plan']['name'], 'Free Trial')
        self.assertEqual(response.data['usage']['projects'], 0)

    def test_checkout_session_creation(self):
        url = f'/api/billing/orgs/{self.org.slug}/status/'
        data = {
            'plan_id': self.pro_plan.id,
            'legal_name': 'Acme Inc',
            'gstin': '29AAAAA1111A1Z1',
            'billing_email': 'billing@acme.com'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('subscription_id', response.data)
        
        # Verify subscription was created in PENDING state
        sub = WorkspaceSubscription.objects.get(organization=self.org)
        self.assertEqual(sub.status, 'PENDING')
        self.assertEqual(sub.legal_name, 'Acme Inc')
        self.assertEqual(sub.gstin, '29AAAAA1111A1Z1')

    def test_payment_verification_success(self):
        # Create pending subscription first
        sub = WorkspaceSubscription.objects.create(
            organization=self.org,
            plan=self.pro_plan,
            razorpay_subscription_id='sub_test_123',
            status='PENDING',
            gstin='29AAAAA1111A1Z1',
            legal_name='Acme Inc'
        )
        
        url = f'/api/billing/orgs/{self.org.slug}/verify-payment/'
        data = {
            'razorpay_payment_id': 'pay_test_999',
            'razorpay_subscription_id': 'sub_test_123',
            'razorpay_signature': 'mock_signature'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        sub.refresh_from_db()
        self.assertEqual(sub.status, 'ACTIVE')
        
        # Verify invoice and payment records are logged
        self.assertTrue(PaymentRecord.objects.filter(razorpay_payment_id='pay_test_999').exists())
        self.assertTrue(InvoiceRecord.objects.filter(subscription=sub).exists())
        inv = InvoiceRecord.objects.get(subscription=sub)
        self.assertEqual(inv.legal_name, 'Acme Inc')
        self.assertEqual(inv.gstin, '29AAAAA1111A1Z1')

    def test_webhook_event_processing(self):
        sub = WorkspaceSubscription.objects.create(
            organization=self.org,
            plan=self.pro_plan,
            razorpay_subscription_id='sub_test_web',
            status='PENDING'
        )

        url = '/api/billing/webhook/'
        payload = {
            'id': 'evt_test_789',
            'event': 'subscription.charged',
            'payload': {
                'subscription': {
                    'entity': {
                        'id': 'sub_test_web'
                    }
                },
                'payment': {
                    'entity': {
                        'id': 'pay_web_111',
                        'amount': 99900 # ₹999 in paise
                    }
                }
            }
        }
        
        # Post webhook with mock signature header
        response = self.client.post(
            url, 
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_RAZORPAY_SIGNATURE='mock_webhook_signature'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        sub.refresh_from_db()
        self.assertEqual(sub.status, 'ACTIVE')
        self.assertTrue(InvoiceRecord.objects.filter(subscription=sub).exists())

    def test_quota_limits_enforcement(self):
        # 1. Project limit check (Free Trial allows 3 projects)
        for i in range(3):
            Project.objects.create(organization=self.org, name=f'Proj {i}')
            
        # Try to perform project create via API (performs perform_create billing check)
        url = f'/api/orgs/{self.org.slug}/projects/'
        response = self.client.post(url, {'name': 'Excess Project'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('limit exceeded', str(response.data[0]).lower())

        # 2. AI generation quota check
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Max out free generations (10 generations)
        UsageEvent.objects.create(organization=self.org, user=self.user, event_type='AI_GENERATION', quantity=10)
        
        # Try to ingest new source (triggers generation limit perform_create check)
        source_url = f'/api/orgs/{self.org.slug}/projects/1/sources/' # project id 1 mock
        # We need a project
        proj = Project.objects.first()
        source_url = f'/api/orgs/{self.org.slug}/projects/{proj.id}/sources/'
        
        response = self.client.post(source_url, {'type': 'ARTICLE', 'title': 'Test', 'text_content': 'Sample'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('limit exceeded', str(response.data[0]).lower())
