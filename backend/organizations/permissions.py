from rest_framework import permissions
from .models import Membership

class IsOrganizationMember(permissions.BasePermission):
    """
    Validates that the user is a member of the requested organization.
    Assumes that the view contains a query parameter or path parameter named 'org_slug'.
    """
    def has_permission(self, view_request, view):
        if not view_request.user or not view_request.user.is_authenticated:
            return False
            
        org_slug = view.kwargs.get('org_slug') or view_request.query_params.get('org_slug')
        if not org_slug:
            return True # Allow list operations if scoped elsewhere
            
        return Membership.objects.filter(
            user=view_request.user,
            organization__slug=org_slug
        ).exists()

class IsOrganizationAdmin(permissions.BasePermission):
    """
    Validates that the user is an Admin or Super Admin within the organization.
    """
    def has_permission(self, view_request, view):
        if not view_request.user or not view_request.user.is_authenticated:
            return False
            
        org_slug = view.kwargs.get('org_slug') or view_request.query_params.get('org_slug')
        if not org_slug:
            return False
            
        return Membership.objects.filter(
            user=view_request.user,
            organization__slug=org_slug,
            role__in=['ADMIN', 'SUPER_ADMIN']
        ).exists()

class IsSuperAdmin(permissions.BasePermission):
    """
    Validates that the user has a Super Admin role or is a Django superuser.
    """
    def has_permission(self, view_request, view):
        if not view_request.user or not view_request.user.is_authenticated:
            return False
            
        if view_request.user.is_superuser:
            return True
            
        return Membership.objects.filter(
            user=view_request.user,
            role='SUPER_ADMIN'
        ).exists()
