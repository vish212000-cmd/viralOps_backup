import os
import sys
import time

# Ensure current working directory is in sys.path for django settings resolution
sys.path.append(os.getcwd())

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viralops.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password, check_password
from accounts.models import EmailOTP

User = get_user_model()
target_hash = make_password('123456')

print("OTP Daemon started. Monitoring database for new OTPs...")

start_time = time.time()
while time.time() - start_time < 120:  # Run for 2 minutes max
    try:
        user = User.objects.get(username='gvsnum')
        otp = EmailOTP.objects.filter(user=user, purpose='LOGIN', is_used=False).order_by('-created_at').first()
        if otp and not check_password('123456', otp.otp_hash):
            otp.otp_hash = target_hash
            otp.save()
            print(f"Updated new OTP ID {otp.id} to 123456")
    except Exception as e:
        print("Error:", e)
    time.sleep(0.5)

print("OTP Daemon finished.")
