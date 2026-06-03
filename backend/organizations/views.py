from rest_framework import status, viewsets, permissions, decorators
from rest_framework.response import Response
from django.utils.text import slugify
from django.shortcuts import get_object_or_404
from .models import Organization, Membership
from projects.serializers import OrganizationSerializer, MembershipSerializer
from projects.models import AuditLog

class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Organization.objects.all()
        return Organization.objects.filter(memberships__user=self.request.user)

    def perform_create(self, serializer):
        name = serializer.validated_data.get('name')
        slug = slugify(name)
        base_slug = slug
        counter = 1
        while Organization.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
            
        org = serializer.save(slug=slug)
        # Creator becomes Workspace Admin (ADMIN)
        Membership.objects.create(
            user=self.request.user,
            organization=org,
            role='ADMIN'
        )
        
        # Log Audit
        AuditLog.objects.create(
            organization=org,
            user=self.request.user,
            action="WORKSPACE_CREATE",
            details={"organization_id": org.id, "name": org.name}
        )

    @decorators.action(detail=True, methods=['get', 'post'])
    def members(self, request, pk=None):
        org = self.get_object()
        if request.method == 'GET':
            memberships = Membership.objects.filter(organization=org)
            serializer = MembershipSerializer(memberships, many=True)
            return Response(serializer.data)
        elif request.method == 'POST':
            # Verify request user is ADMIN or SUPER_ADMIN
            user_membership = get_object_or_404(Membership, user=request.user, organization=org)
            if user_membership.role not in ['ADMIN', 'SUPER_ADMIN'] and not request.user.is_superuser:
                return Response({'detail': 'Only admins can invite members.'}, status=status.HTTP_403_FORBIDDEN)
                
            username = request.data.get('username')
            role = request.data.get('role', 'MEMBER')
            from django.contrib.auth import get_user_model
            User = get_user_model()
            target_user = get_object_or_404(User, username=username)
            
            membership, created = Membership.objects.get_or_create(
                user=target_user,
                organization=org,
                defaults={'role': role}
            )
            if not created:
                membership.role = role
                membership.save()
                
            AuditLog.objects.create(
                organization=org,
                user=request.user,
                action="MEMBER_INVITE",
                details={"invited_username": username, "role": role}
            )
            
            serializer = MembershipSerializer(membership)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
