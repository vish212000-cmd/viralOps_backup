
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "viralops.settings.local")
django.setup()
from django.contrib.auth import get_user_model
from organizations.models import Organization, Membership
User = get_user_model()
User.objects.filter(username="rbac_user_a").delete()
user_a = User.objects.create_user(username="rbac_user_a", email="rbac_a@viralops.com", password="pass123a")
if hasattr(user_a, "is_email_verified"): user_a.is_email_verified = True
user_a.save()
org_a, _ = Organization.objects.get_or_create(slug="rbac-org-a", defaults={"name":"RBAC Org A"})
Membership.objects.get_or_create(organization=org_a, user=user_a, defaults={"role":"ADMIN"})
User.objects.filter(username="rbac_user_b").delete()
user_b = User.objects.create_user(username="rbac_user_b", email="rbac_b@viralops.com", password="pass123b")
if hasattr(user_b, "is_email_verified"): user_b.is_email_verified = True
user_b.save()
org_b, _ = Organization.objects.get_or_create(slug="rbac-org-b", defaults={"name":"RBAC Org B"})
Membership.objects.get_or_create(organization=org_b, user=user_b, defaults={"role":"ADMIN"})
print(f"Org A slug: {org_a.slug}")
print(f"Org B slug: {org_b.slug}")
