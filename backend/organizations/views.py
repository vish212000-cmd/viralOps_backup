from rest_framework import status, viewsets, permissions, decorators, views
from rest_framework.response import Response
from django.utils.text import slugify
from django.shortcuts import get_object_or_404
from .models import Organization, Membership, WorkspaceInvite
from projects.serializers import OrganizationSerializer, MembershipSerializer
from projects.models import AuditLog
from accounts.views import send_invite_email

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

    @decorators.action(detail=True, methods=['post'])
    def invite(self, request, pk=None):
        org = self.get_object()
        
        # Verify request user is ADMIN or SUPER_ADMIN
        user_membership = get_object_or_404(Membership, user=request.user, organization=org)
        if user_membership.role not in ['ADMIN', 'SUPER_ADMIN'] and not request.user.is_superuser:
            return Response({'detail': 'Only admins can invite members.'}, status=status.HTTP_403_FORBIDDEN)
            
        email = request.data.get('email')
        role = request.data.get('role', 'MEMBER')
        
        if not email:
            return Response({'email': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)
            
        if role not in [r[0] for r in Membership.ROLE_CHOICES]:
            return Response({'role': 'Invalid role choice.'}, status=status.HTTP_400_BAD_REQUEST)
            
        invite, created = WorkspaceInvite.objects.update_or_create(
            organization=org,
            email=email.strip().lower(),
            defaults={'role': role, 'invited_by': request.user, 'accepted': False}
        )
        
        try:
            send_invite_email(invite)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send invite email to {email}: {str(e)}")
            
        AuditLog.objects.create(
            organization=org,
            user=request.user,
            action="MEMBER_INVITE_SENT",
            details={"invited_email": email, "role": role}
        )
        
        return Response({'message': 'Invitation sent successfully.'}, status=status.HTTP_201_CREATED)

    @decorators.action(detail=True, methods=['get', 'put', 'patch'])
    def brand_kit(self, request, pk=None):
        org = self.get_object()
        from organizations.models import BrandKit
        from projects.serializers import BrandKitSerializer
        
        brand_kit, created = BrandKit.objects.get_or_create(organization=org)
        
        if request.method == 'GET':
            serializer = BrandKitSerializer(brand_kit)
            return Response(serializer.data)
            
        elif request.method in ['PUT', 'PATCH']:
            # Verify request user is ADMIN or SUPER_ADMIN
            user_membership = get_object_or_404(Membership, user=request.user, organization=org)
            if user_membership.role not in ['ADMIN', 'SUPER_ADMIN'] and not request.user.is_superuser:
                return Response({'detail': 'Only admins can update the Brand Kit.'}, status=status.HTTP_403_FORBIDDEN)
                
            serializer = BrandKitSerializer(brand_kit, data=request.data, partial=(request.method == 'PATCH'))
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AcceptWorkspaceInviteView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({'error': 'Token is required.'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            invite = WorkspaceInvite.objects.get(id=token, accepted=False)
            
            # Enforce matching emails
            if request.user.email.strip().lower() != invite.email.strip().lower():
                return Response(
                    {'error': f'This invitation was sent to {invite.email}. Please use the correct email address.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            membership, created = Membership.objects.get_or_create(
                user=request.user,
                organization=invite.organization,
                defaults={'role': invite.role}
            )
            if not created:
                membership.role = invite.role
                membership.save()
                
            invite.accepted = True
            invite.save()
            
            AuditLog.objects.create(
                organization=invite.organization,
                user=request.user,
                action="WORKSPACE_INVITE_ACCEPTED",
                details={"user": request.user.username, "role": invite.role}
            )
            
            return Response({
                'message': 'Invitation accepted successfully.',
                'organization': {
                    'id': invite.organization.id,
                    'name': invite.organization.name,
                    'slug': invite.organization.slug
                }
            }, status=status.HTTP_200_OK)
            
        except (WorkspaceInvite.DoesNotExist, ValueError):
            return Response({'error': 'Invalid or expired invitation token.'}, status=status.HTTP_400_BAD_REQUEST)
