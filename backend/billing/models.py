from django.db import models
from django.conf import settings
from organizations.mixins import TenantScopedQuerysetMixin

class SubscriptionPlan(TenantScopedQuerysetMixin, models.Model):
    tenant = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, null=True, blank=True)
    PLAN_CHOICES = (('FREE', 'Free'), ('PRO', 'Pro'), ('TEAMS', 'Teams'), ('ENTERPRISE', 'Enterprise'))
    name = models.CharField(max_length=50, choices=PLAN_CHOICES, unique=True)
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_yearly = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    razorpay_plan_id = models.CharField(max_length=100, blank=True)
    max_projects = models.IntegerField(default=5)
    max_generations_per_month = models.IntegerField(default=100)
    max_storage_gb = models.IntegerField(default=10)
    ai_brand_tone = models.BooleanField(default=False)
    custom_domain = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_name_display()} Plan"

class Subscription(TenantScopedQuerysetMixin, models.Model):
    tenant = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    razorpay_subscription_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    razorpay_customer_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=(
        ('ACTIVE', 'Active'), ('PAST_DUE', 'Past Due'), 
        ('CANCELLED', 'Cancelled'), ('PENDING', 'Pending')
    ), default='PENDING')
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancel_reason = models.TextField(blank=True)
    # India-ready Tax & Legal Compliance details
    legal_name = models.CharField(max_length=255, blank=True, default='')
    billing_contact = models.CharField(max_length=100, blank=True, default='')
    billing_email = models.EmailField(blank=True, default='')
    billing_address = models.TextField(blank=True, default='')
    gstin = models.CharField(max_length=15, blank=True, default='')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('tenant', 'user')

    def __str__(self):
        return f"{self.tenant.name} - {self.plan.name} ({self.status})"

class Invoice(TenantScopedQuerysetMixin, models.Model):
    tenant = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    razorpay_invoice_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    status = models.CharField(max_length=20, choices=(
        ('GENERATED', 'Generated'), ('PAID', 'Paid'),
        ('FAILED', 'Failed'), ('VOID', 'Void')
    ), default='GENERATED')
    paid_at = models.DateTimeField(null=True, blank=True)
    pdf_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice {self.razorpay_invoice_id or self.id} ({self.amount} {self.currency})"

class PaymentTransaction(TenantScopedQuerysetMixin, models.Model):
    tenant = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    razorpay_payment_id = models.CharField(max_length=100)
    razorpay_order_id = models.CharField(max_length=100)
    razorpay_signature = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    status = models.CharField(max_length=20, choices=(
        ('CAPTURED', 'Captured'), ('FAILED', 'Failed'), 
        ('REFUNDED', 'Refunded'), ('AUTHORIZED', 'Authorized')
    ))
    captured_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Tx {self.razorpay_payment_id} ({self.amount} {self.currency})"
