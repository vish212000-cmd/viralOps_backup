
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viralops.settings.local')
django.setup()
from accounts.models import EmailOTP, User
from django.contrib.auth.hashers import make_password, check_password
u = User.objects.get(username='admin')
otp_record = EmailOTP.objects.filter(user=u, purpose='LOGIN').order_by('-created_at').first()
# We can't unhash it, but we can set the hash of '123456'
otp_record.otp_hash = make_password('123456')
otp_record.save()
print("123456")
