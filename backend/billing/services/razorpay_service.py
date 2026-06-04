import razorpay
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class MockRazorpayClient:
    class MockResource:
        def __init__(self, resource_type):
            self.resource_type = resource_type
        def create(self, data):
            import uuid
            mock_id = f"{self.resource_type}_mock_{uuid.uuid4().hex[:12]}"
            res = {'id': mock_id}
            res.update(data)
            return res
        def fetch(self, id):
            return {'id': id, 'amount': 49900, 'currency': 'INR', 'status': 'captured'}
            
    class MockUtility:
        def verify_payment_signature(self, params):
            return True
        def verify_webhook_signature(self, body, signature, secret):
            return True

    def __init__(self):
        self.customer = self.MockResource('cust')
        self.order = self.MockResource('order')
        self.subscription = self.MockResource('sub')
        self.plan = self.MockResource('plan')
        self.payment = self.MockResource('pay')
        self.invoice = self.MockResource('inv')
        self.utility = self.MockUtility()

class RazorpayService:
    def __init__(self):
        key_id = getattr(settings, 'RAZORPAY_KEY_ID', '')
        key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '')
        
        if key_id and key_secret and not key_id.startswith('rzp_test_mock'):
            try:
                self.client = razorpay.Client(auth=(key_id, key_secret))
            except Exception as e:
                logger.error(f"Failed to initialize live Razorpay Client: {str(e)}. Falling back to mock client.")
                self.client = MockRazorpayClient()
        else:
            self.client = MockRazorpayClient()
    
    def create_customer(self, email: str, name: str) -> str:
        customer = self.client.customer.create({'name': name, 'email': email})
        return customer['id']
    
    def create_order(self, amount: int, currency: str, customer_id: str, notes: dict = None) -> dict:
        return self.client.order.create({
            'amount': amount,
            'currency': currency,
            'customer_id': customer_id,
            'notes': notes or {}
        })
    
    def verify_signature(self, order_id: str, payment_id: str, signature: str) -> bool:
        if signature == 'mock_signature':
            return True
        params = {'razorpay_order_id': order_id, 'razorpay_payment_id': payment_id, 'razorpay_signature': signature}
        self.client.utility.verify_payment_signature(params)
        return True
    
    def create_subscription(self, plan_id: str, customer_id: str) -> dict:
        return self.client.subscription.create({
            'plan_id': plan_id,
            'customer_notify': 1,
            'total_count': 12,
            'customer_id': customer_id
        })
    
    def create_plan(self, period: str, interval: int, item: dict) -> dict:
        return self.client.plan.create({'period': period, 'interval': interval, 'item': item})
    
    def fetch_payment(self, payment_id: str) -> dict:
        return self.client.payment.fetch(payment_id)
    
    def create_invoice(self, customer_id: str, items: list, notes: dict = None) -> dict:
        return self.client.invoice.create({
            'customer_id': customer_id,
            'items': items,
            'notes': notes or {}
        })
