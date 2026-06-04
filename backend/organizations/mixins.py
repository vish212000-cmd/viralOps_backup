from rest_framework import exceptions
from organizations.models import Organization, Membership

class TenantScopedQuerysetMixin:
    """
    Mixin that filters querysets to objects belonging to the active organization.
    Ensures perfect tenant isolation across Projects, Sources, Assets, etc.
    """
    def get_organization(self):
        org_slug = self.kwargs.get('org_slug') or self.request.query_params.get('org_slug')
        if not org_slug:
            # Check headers just in case
            org_slug = self.request.headers.get('X-Org-Slug')
            
        if not org_slug:
            # Fall back to user's first organization
            membership = Membership.objects.filter(user=self.request.user).first()
            if membership:
                return membership.organization
            raise exceptions.ValidationError({"org_slug": "An organization slug is required."})
        
        try:
            return Organization.objects.get(slug=org_slug)
        except Organization.DoesNotExist:
            raise exceptions.NotFound("Organization not found.")

    def get_queryset(self):
        org = self.get_organization()
        
        # Verify user belongs to org (except Django superusers)
        if not self.request.user.is_superuser:
            if not Membership.objects.filter(user=self.request.user, organization=org).exists():
                raise exceptions.PermissionDenied("You do not belong to this organization.")
                
        queryset = super().get_queryset()
        model = queryset.model
        
        # Scope queryset by organization key relationship
        if hasattr(model, 'organization'):
            return queryset.filter(organization=org)
        elif hasattr(model, 'tenant'):
            return queryset.filter(tenant=org)
        elif hasattr(model, 'project'):
            return queryset.filter(project__organization=org)
        elif hasattr(model, 'source_input'):
            return queryset.filter(source_input__project__organization=org)
        
        return queryset
