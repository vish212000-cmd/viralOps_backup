from rest_framework import serializers
from .models import SubscriptionPlan, Subscription, Invoice, PaymentTransaction

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'
        read_only_fields = [f.name for f in SubscriptionPlan._meta.fields]

class SubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    plan_id = serializers.PrimaryKeyRelatedField(
        queryset=SubscriptionPlan.objects.all(), source='plan', write_only=True
    )

    class Meta:
        model = Subscription
        fields = (
            'id', 'tenant', 'user', 'plan', 'plan_id', 
            'razorpay_subscription_id', 'razorpay_customer_id', 'status',
            'current_period_start', 'current_period_end', 'cancelled_at', 
            'cancel_reason', 'legal_name', 'billing_contact', 'billing_email', 
            'billing_address', 'gstin', 'created_at', 'updated_at'
        )
        read_only_fields = (
            'tenant', 'user', 'razorpay_subscription_id', 'razorpay_customer_id',
            'status', 'current_period_start', 'current_period_end', 'cancelled_at',
            'cancel_reason', 'created_at', 'updated_at'
        )

class InvoiceSerializer(serializers.ModelSerializer):
    invoice_number = serializers.SerializerMethodField()
    tax_amount = serializers.SerializerMethodField()
    gstin = serializers.SerializerMethodField()
    legal_name = serializers.SerializerMethodField()
    billing_address = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = [f.name for f in Invoice._meta.fields]

    def get_invoice_number(self, obj):
        return obj.razorpay_invoice_id or f"INV-{obj.tenant.id}-{obj.id}"

    def get_tax_amount(self, obj):
        from decimal import Decimal
        return str(round(obj.amount * Decimal('0.18'), 2))

    def get_gstin(self, obj):
        return obj.subscription.gstin if hasattr(obj.subscription, 'gstin') else ''

    def get_legal_name(self, obj):
        return obj.subscription.legal_name if hasattr(obj.subscription, 'legal_name') else ''

    def get_billing_address(self, obj):
        return obj.subscription.billing_address if hasattr(obj.subscription, 'billing_address') else ''

class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = '__all__'
        read_only_fields = [f.name for f in PaymentTransaction._meta.fields]

class CreateSubscriptionSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()

class VerifyPaymentSerializer(serializers.Serializer):
    order_id = serializers.CharField(max_length=100)
    payment_id = serializers.CharField(max_length=100)
    signature = serializers.CharField(max_length=200)
