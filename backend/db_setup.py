
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "viralops.settings.local")
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.filter(username="admin").delete()
user = User.objects.create_user(username="admin", email="admin@viralops.com", password="admin123")
if hasattr(user, "is_email_verified"): user.is_email_verified = True
user.save()
print(f"User created: id={user.id}")
