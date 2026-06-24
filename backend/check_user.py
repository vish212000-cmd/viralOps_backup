import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viralops.settings.local')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
u = User.objects.get(username='admin')
print(f'Active: {u.is_active}, Verified: {getattr(u, "is_email_verified", None)}')
