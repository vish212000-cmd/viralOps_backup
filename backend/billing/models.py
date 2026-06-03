from django.db import models
from django.conf import settings
from organizations.models import Organization

class Plan(models.Model):
    INTERVAL_CHOICES = [
        ('MONTHLY', 'Monthly'),
        ('YEARLY', 'Yearly'),
    ]
    name = models.CharField(max_length=255)
    razorpay_plan_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price in INR")
    currency = models.CharField(max_length=10, default='INR')
    interval = models.CharField(max_length=20, choices=INTERVAL_CHOICES, default='MONTHLY')
    quota_projects = models.IntegerField(default=3, help_text="Maximum allowed projects")
    quota_generations = models.IntegerField(default=10, help_text="Maximum allowed AI generations per month")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.price} {self.currency}/{self.interval}"

class WorkspaceSubscription(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Payment'),
        ('ACTIVE', 'Active'),
        ('CANCELLED', 'Cancelled'),
        ('EXPIRED', 'Expired'),
        ('HALTED', 'Halted'),
    ]
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='subscriptions')
    razorpay_subscription_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    
    # India-ready Tax & Legal Compliance details
    legal_name = models.CharField(max_length=255, blank=True, default='', help_text="Registered Company/Entity Name")
    billing_contact = models.CharField(max_length=100, blank=True, default='')
    billing_email = models.EmailField(blank=True, default='')
    billing_address = models.TextField(blank=True, default='')
    gstin = models.CharField(max_length=15, blank=True, default='', help_text="15-digit GSTIN ID")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.organization.name} - {self.plan.name} ({self.status})"

class PaymentRecord(models.Model):
    STATUS_CHOICES = [
        ('CAPTURED', 'Captured / Success'),
        ('FAILED', 'Failed'),
        ('PENDING', 'Pending'),
    ]
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='payments')
    razorpay_payment_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    razorpay_order_id = models.CharField(max_length=255, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=255, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='INR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        id_str = self.razorpay_payment_id or f"Order:{self.razorpay_order_id}"
        return f"Payment {id_str} ({self.amount} INR) - {self.status}"

class InvoiceRecord(models.Model):
    subscription = models.ForeignKey(WorkspaceSubscription, on_delete=models.CASCADE, related_name='invoices')
    invoice_number = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="18% GST Amount")
    
    # Snapshot at time of payment
    gstin = models.CharField(max_length=15, blank=True, default='')
    legal_name = models.CharField(max_length=255, blank=True, default='')
    billing_address = models.TextField(blank=True, default='')
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice {self.invoice_number} ({self.amount} INR)"

class WebhookEventLog(models.Model):
    event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=255)
    payload = models.JSONField()
    processed = models.BooleanField(default=False)
    error_log = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Webhook {self.event_id} ({self.event_type}) - Processed: {self.processed}"
