from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from .models import Organization, Membership, WorkspaceInvite

User = get_user_model()

class WorkspaceInvitationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            username='org_owner', email='owner@viralops.com', password='password123', is_email_verified=True
        )
        self.org = Organization.objects.create(name='Test Workspace', slug='test-workspace')
        self.owner_membership = Membership.objects.create(
            user=self.owner, organization=self.org, role='ADMIN'
        )
        
        self.invite_url = reverse('organization-invite', args=[self.org.id])
        self.accept_url = reverse('accept-invite')

    def test_send_invite_by_admin(self):
        self.client.force_authenticate(user=self.owner)
        mail.outbox = []
        
        payload = {
            'email': 'invitee@viralops.com',
            'role': 'MEMBER'
        }
        res = self.client.post(self.invite_url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        
        # Verify invite model exists
        invite = WorkspaceInvite.objects.get(organization=self.org, email='invitee@viralops.com')
        self.assertEqual(invite.role, 'MEMBER')
        self.assertEqual(invite.invited_by, self.owner)
        self.assertFalse(invite.accepted)
        
        # Verify invite email sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Invitation to join Test Workspace", mail.outbox[0].subject)

    def test_accept_invite_matching_email(self):
        # Create an invite
        invite = WorkspaceInvite.objects.create(
            organization=self.org,
            email='invitee@viralops.com',
            role='MEMBER',
            invited_by=self.owner
        )
        
        # Create and authenticate user with matching email
        invitee = User.objects.create_user(
            username='invitee', email='invitee@viralops.com', password='password123', is_email_verified=True
        )
        self.client.force_authenticate(user=invitee)
        
        payload = {'token': str(invite.id)}
        res = self.client.post(self.accept_url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        # Verify membership is created
        membership = Membership.objects.get(user=invitee, organization=self.org)
        self.assertEqual(membership.role, 'MEMBER')
        
        # Verify invite is marked accepted
        invite.refresh_from_db()
        self.assertTrue(invite.accepted)

    def test_accept_invite_mismatch_email_fails(self):
        # Create an invite
        invite = WorkspaceInvite.objects.create(
            organization=self.org,
            email='invitee@viralops.com',
            role='MEMBER',
            invited_by=self.owner
        )
        
        # Create and authenticate user with different email
        wrong_user = User.objects.create_user(
            username='wrong_user', email='wrong@viralops.com', password='password123', is_email_verified=True
        )
        self.client.force_authenticate(user=wrong_user)
        
        payload = {'token': str(invite.id)}
        res = self.client.post(self.accept_url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', res.data)
        
        # Verify no membership is created for wrong user
        self.assertFalse(Membership.objects.filter(user=wrong_user, organization=self.org).exists())
