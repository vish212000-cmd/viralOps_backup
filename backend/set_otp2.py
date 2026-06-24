
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "viralops.settings.local")
django.setup()
from accounts.models import EmailOTP
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
u = get_user_model().objects.get(username="admin")
otp = EmailOTP.objects.filter(user=u, purpose="LOGIN").order_by("-created_at").first()
if otp: otp.otp_hash = make_password("123456"); otp.save()
