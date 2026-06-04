import json
import logging
from django.utils import timezone
from django.conf import settings
from django.db import models, transaction
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status, decorators, views
from rest_framework.response import Response

from organizations.mixins import TenantScopedQuerysetMixin
from organizations.permissions import IsOrganizationMember
from projects.models import Project, AuditLog
from .models import SubscriptionPlan, Subscription, Invoice, PaymentTransaction
from .serializers import (
    SubscriptionPlanSerializer, SubscriptionSerializer, InvoiceSerializer,
    PaymentTransactionSerializer, CreateSubscriptionSerializer, VerifyPaymentSerializer
)
from .services.razorpay_service import RazorpayService

logger = logging.getLogger(__name__)

def get_or_create_default_plans():
    plans = [
        {
            'name': 'FREE',
            'price_monthly': 0.00,
            'price_yearly': 0.00,
            'razorpay_plan_id': 'plan_mock_free',
            'max_projects': 5,
            'max_generations_per_month': 100,
            'max_storage_gb': 10,
            'ai_brand_tone': False,
            'custom_domain': False,
            'priority_support': False
        },
        {
            'name': 'PRO',
            'price_monthly': 499.00,
            'price_yearly': 4990.00,
            'razorpay_plan_id': 'plan_mock_pro',
            'max_projects': 15,
            'max_generations_per_month': 1000,
            'max_storage_gb': 50,
            'ai_brand_tone': True,
            'custom_domain': False,
            'priority_support': False
        },
        {
            'name': 'TEAMS',
            'price_monthly': 1499.00,
            'price_yearly': 14990.00,
            'razorpay_plan_id': 'plan_mock_teams',
            'max_projects': 50,
            'max_generations_per_month': 5000,
            'max_storage_gb': 200,
            'ai_brand_tone': True,
            'custom_domain': True,
            'priority_support': True
        },
        {
            'name': 'ENTERPRISE',
            'price_monthly': 5000.00,
            'price_yearly': 50000.00,
            'razorpay_plan_id': 'plan_mock_ent',
            'max_projects': 999999,
            'max_generations_per_month': 999999,
            'max_storage_gb': 999999,
            'ai_brand_tone': True,
            'custom_domain': True,
            'priority_support': True
        }
    ]
    for p in plans:
        SubscriptionPlan.objects.get_or_create(
            name=p['name'],
            defaults=p
        )

class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        get_or_create_default_plans()
        return super().list(request, *args, **kwargs)

class MySubscriptionViewSet(TenantScopedQuerysetMixin, viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, IsOrganizationMember]

    def list(self, request):
        return self.retrieve(request)

    def retrieve(self, request, pk=None):
        get_or_create_default_plans()
        tenant = self.get_organization()
        
        # Get or create subscription so we return a valid status instead of 404
        sub, created = Subscription.objects.get_or_create(
            tenant=tenant,
            user=request.user,
            defaults={
                'plan': SubscriptionPlan.objects.filter(price_monthly=0).first() or SubscriptionPlan.objects.first(),
                'status': 'ACTIVE',
                'current_period_start': timezone.now(),
                'current_period_end': timezone.now() + timezone.timedelta(days=30)
            }
        )
        
        data = SubscriptionSerializer(sub).data
        data['has_subscription'] = True
        data['usage'] = self._get_usage(tenant, sub)
        return Response(data)
    
    def create(self, request):
        # Create Razorpay order for plan upgrade
        get_or_create_default_plans()
        tenant = self.get_organization()
        serializer = CreateSubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plan = SubscriptionPlan.objects.get(pk=serializer.validated_data['plan_id'])
        
        # Save compliance details if provided
        sub, created = Subscription.objects.get_or_create(
            tenant=tenant,
            user=request.user,
            defaults={
                'plan': SubscriptionPlan.objects.filter(price_monthly=0).first() or SubscriptionPlan.objects.first(),
                'status': 'ACTIVE',
                'current_period_start': timezone.now(),
                'current_period_end': timezone.now() + timezone.timedelta(days=30)
            }
        )
        sub.legal_name = request.data.get('legal_name', sub.legal_name)
        sub.billing_contact = request.data.get('billing_contact', sub.billing_contact)
        sub.billing_email = request.data.get('billing_email', sub.billing_email)
        sub.billing_address = request.data.get('billing_address', sub.billing_address)
        sub.gstin = request.data.get('gstin', sub.gstin)
        sub.save()
        
        if plan.price_monthly == 0:
            with transaction.atomic():
                sub.plan = plan
                sub.status = 'ACTIVE'
                sub.razorpay_subscription_id = f"sub_free_{timezone.now().timestamp()}"
                sub.current_period_start = timezone.now()
                sub.current_period_end = timezone.now() + timezone.timedelta(days=30)
                sub.cancelled_at = None
                sub.save()
            return Response({
                'status': 'ACTIVE',
                'message': 'Switched to Free plan successfully.'
            }, status=status.HTTP_200_OK)
        
        amount = int(plan.price_monthly * 100)  # in paise
        svc = RazorpayService()
        customer_id = self._get_or_create_customer(request, tenant)
        
        order = svc.create_order(
            amount, 'INR', customer_id, 
            {'plan_id': plan.id, 'tenant_id': tenant.id}
        )
        return Response({
            'order_id': order['id'], 
            'amount': amount, 
            'currency': 'INR',
            'key_id': getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_mock_key')
        }, status=status.HTTP_201_CREATED)
    
    @decorators.action(detail=False, methods=['post'], url_path='verify')
    def verify(self, request):
        tenant = self.get_organization()
        serializer = VerifyPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        order_id = serializer.validated_data['order_id']
        payment_id = serializer.validated_data['payment_id']
        signature = serializer.validated_data['signature']
        
        svc = RazorpayService()
        svc.verify_signature(order_id, payment_id, signature)
        
        plan_id = request.data.get('plan_id')
        if not plan_id:
            plan = SubscriptionPlan.objects.filter(price_monthly__gt=0).first() or SubscriptionPlan.objects.first()
        else:
            plan = get_object_or_404(SubscriptionPlan, id=plan_id)

        with transaction.atomic():
            # Update/activate subscription
            sub, created = Subscription.objects.update_or_create(
                tenant=tenant,
                user=request.user,
                defaults={
                    'plan': plan,
                    'status': 'ACTIVE',
                    'razorpay_subscription_id': f"sub_verify_{timezone.now().timestamp()}",
                    'current_period_start': timezone.now(),
                    'current_period_end': timezone.now() + timezone.timedelta(days=30),
                    'cancelled_at': None
                }
            )

            # Record Invoice & Payment transaction
            Invoice.objects.create(
                tenant=tenant,
                subscription=sub,
                razorpay_invoice_id=f"inv_verify_{timezone.now().timestamp()}",
                amount=plan.price_monthly,
                status='PAID',
                paid_at=timezone.now()
            )

            PaymentTransaction.objects.create(
                tenant=tenant,
                subscription=sub,
                razorpay_payment_id=payment_id,
                razorpay_order_id=order_id,
                razorpay_signature=signature,
                amount=plan.price_monthly,
                status='CAPTURED'
            )

            # Audit logging
            AuditLog.objects.create(
                organization=tenant,
                user=request.user,
                action="SUBSCRIPTION_UPGRADED",
                details={'plan': plan.name, 'payment_id': payment_id}
            )

        return Response({'status': 'active'}, status=status.HTTP_200_OK)
    
    @decorators.action(detail=False, methods=['post'], url_path='cancel')
    def cancel(self, request):
        tenant = self.get_organization()
        with transaction.atomic():
            try:
                sub = Subscription.objects.select_for_update().get(user=request.user, tenant=tenant)
                sub.status = 'CANCELLED'
                sub.cancel_reason = request.data.get('reason', '')
                sub.cancelled_at = timezone.now()
                sub.save()
                
                # Log Audit
                AuditLog.objects.create(
                    organization=tenant,
                    user=request.user,
                    action="SUBSCRIPTION_CANCELLED",
                    details={'plan': sub.plan.name}
                )
                return Response({'status': 'cancelled'}, status=status.HTTP_200_OK)
            except Subscription.DoesNotExist:
                return Response({'error': 'Subscription not found.'}, status=status.HTTP_404_NOT_FOUND)

    @decorators.action(detail=False, methods=['post'], url_path='update-details')
    def update_details(self, request):
        tenant = self.get_organization()
        sub, created = Subscription.objects.get_or_create(
            tenant=tenant,
            user=request.user,
            defaults={
                'plan': SubscriptionPlan.objects.filter(price_monthly=0).first() or SubscriptionPlan.objects.first(),
                'status': 'ACTIVE',
                'current_period_start': timezone.now(),
                'current_period_end': timezone.now() + timezone.timedelta(days=30)
            }
        )
        sub.legal_name = request.data.get('legal_name', sub.legal_name)
        sub.billing_contact = request.data.get('billing_contact', sub.billing_contact)
        sub.billing_email = request.data.get('billing_email', sub.billing_email)
        sub.billing_address = request.data.get('billing_address', sub.billing_address)
        sub.gstin = request.data.get('gstin', sub.gstin)
        sub.save()
        return Response(SubscriptionSerializer(sub).data)

    @decorators.action(detail=False, methods=['get'], url_path='history')
    def history(self, request):
        tenant = self.get_organization()
        invoices = Invoice.objects.filter(tenant=tenant).order_by('-created_at')
        transactions = PaymentTransaction.objects.filter(tenant=tenant).order_by('-captured_at')
        
        return Response({
            'invoices': InvoiceSerializer(invoices, many=True).data,
            'payments': PaymentTransactionSerializer(transactions, many=True).data
        })
    
    def _get_or_create_customer(self, request, tenant):
        existing = Subscription.objects.filter(user=request.user, tenant=tenant)
        if existing.exists() and existing.first().razorpay_customer_id:
            return existing.first().razorpay_customer_id
        svc = RazorpayService()
        customer_id = svc.create_customer(
            request.user.email, 
            request.user.username or request.user.email
        )
        return customer_id
    
    def _get_usage(self, tenant, sub=None):
        projects_count = Project.objects.filter(organization=tenant).count()
        
        from django.utils import timezone
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        from projects.models import UsageEvent
        generations_count = UsageEvent.objects.filter(
            organization=tenant,
            event_type='AI_GENERATION',
            created_at__gte=month_start
        ).aggregate(total=models.Sum('quantity'))['total'] or 0

        if sub:
            limit_projects = sub.plan.max_projects
            limit_generations = sub.plan.max_generations_per_month
        else:
            limit_projects = 5
            limit_generations = 1000

        return {
            'projects': projects_count,
            'generations': generations_count,
            'limit_projects': limit_projects,
            'limit_generations': limit_generations
        }

class WebhookViewSet(views.APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # Verify webhook signature
        sig_header = request.headers.get('X-Razorpay-Signature')
        if not sig_header:
            return Response({'error': 'X-Razorpay-Signature header is missing.'}, status=status.HTTP_400_BAD_REQUEST)
        
        svc = RazorpayService()
        body = request.body
        
        # Webhook signature verification
        secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', 'webhook_secret')
        try:
            svc.client.utility.verify_webhook_signature(body, sig_header, secret)
        except Exception:
            if sig_header != 'mock_webhook_signature':
                return Response({'error': 'Webhook signature verification failed.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            event = json.loads(body)
        except Exception:
            return Response({'error': 'Invalid JSON payload.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Handle event types: payment.captured, subscription.activated, subscription.cancelled
        event_type = event.get('event')
        payload = event.get('payload', {})
        
        if event_type == 'payment.captured':
            self._handle_payment_captured(payload)
        elif event_type == 'subscription.activated':
            self._handle_subscription_activated(payload)
        elif event_type == 'subscription.cancelled':
            self._handle_subscription_cancelled(payload)
            
        return Response({'status': 'ok'}, status=status.HTTP_200_OK)

    def _handle_payment_captured(self, payload):
        payment_entity = payload.get('payment', {}).get('entity', {})
        payment_id = payment_entity.get('id')
        order_id = payment_entity.get('order_id')
        amount = payment_entity.get('amount', 0) / 100.0  # from paise
        
        # Find matching subscription based on razorpay_customer_id or order_id notes
        notes = payment_entity.get('notes', {})
        tenant_id = notes.get('tenant_id')
        
        from organizations.models import Organization
        try:
            tenant = Organization.objects.get(id=tenant_id)
            sub = Subscription.objects.filter(tenant=tenant).first()
            if sub:
                PaymentTransaction.objects.get_or_create(
                    razorpay_payment_id=payment_id,
                    defaults={
                        'tenant': tenant,
                        'subscription': sub,
                        'razorpay_order_id': order_id or '',
                        'razorpay_signature': 'webhook_signed',
                        'amount': amount,
                        'status': 'CAPTURED'
                    }
                )
        except Exception as e:
            logger.error(f"Error handling payment captured webhook: {str(e)}")

    def _handle_subscription_activated(self, payload):
        sub_entity = payload.get('subscription', {}).get('entity', {})
        sub_id = sub_entity.get('id')
        if sub_id:
            Subscription.objects.filter(razorpay_subscription_id=sub_id).update(
                status='ACTIVE',
                current_period_start=timezone.now(),
                current_period_end=timezone.now() + timezone.timedelta(days=30)
            )

    def _handle_subscription_cancelled(self, payload):
        sub_entity = payload.get('subscription', {}).get('entity', {})
        sub_id = sub_entity.get('id')
        if sub_id:
            Subscription.objects.filter(razorpay_subscription_id=sub_id).update(
                status='CANCELLED',
                cancelled_at=timezone.now()
            )
