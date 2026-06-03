from rest_framework import serializers
from .models import Plan, WorkspaceSubscription, PaymentRecord, InvoiceRecord

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = '__all__'

class WorkspaceSubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)

    class Meta:
        model = WorkspaceSubscription
        fields = (
            'id', 'organization', 'plan', 'razorpay_subscription_id', 
            'status', 'start_date', 'end_date', 'legal_name', 'billing_contact', 
            'billing_email', 'billing_address', 'gstin', 'created_at', 'updated_at'
        )
        read_only_fields = ('organization', 'razorpay_subscription_id', 'status', 'start_date', 'end_date')

class PaymentRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentRecord
        fields = '__all__'

class InvoiceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceRecord
        fields = '__all__'
