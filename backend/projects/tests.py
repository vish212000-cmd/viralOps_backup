from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from organizations.models import Organization, Membership
from projects.models import (
    Project, SourceInput, TranscriptRecord, GeneratedAsset,
    GeneratedAssetVersion, AuditLog, UsageEvent
)

User = get_user_model()

class TenantSeparationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # User 1 and Organization 1
        self.user1 = User.objects.create_user(username='user1', email='user1@viralops.com', password='password123')
        self.org1 = Organization.objects.create(name='Org One', slug='org-one')
        self.membership1 = Membership.objects.create(user=self.user1, organization=self.org1, role='MEMBER')
        
        # User 2 and Organization 2
        self.user2 = User.objects.create_user(username='user2', email='user2@viralops.com', password='password123')
        self.org2 = Organization.objects.create(name='Org Two', slug='org-two')
        self.membership2 = Membership.objects.create(user=self.user2, organization=self.org2, role='MEMBER')
        
        # Create Project under Org 1
        self.proj1 = Project.objects.create(organization=self.org1, name='Org 1 Project', description='Secret')
        
        # Create Project under Org 2
        self.proj2 = Project.objects.create(organization=self.org2, name='Org 2 Project', description='Private')

    def test_tenant_scoping_isolation(self):
        """
        Ensure User 1 cannot access or view Project 2 belonging to Organization 2.
        """
        # Authenticate User 1
        self.client.force_authenticate(user=self.user1)
        
        # Set Header slug for Org 1
        self.client.defaults['HTTP_X_ORG_SLUG'] = self.org1.slug
        
        # Fetch projects list
        url = reverse('project-list', kwargs={'org_slug': self.org1.slug})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only return proj1
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Org 1 Project')
        
        # Try to access proj2 detail belonging to Org 2
        url_detail = reverse('project-detail', kwargs={'org_slug': self.org1.slug, 'pk': self.proj2.id})
        response_detail = self.client.get(url_detail)
        
        # Should fail with PermissionDenied or NotFound (which is more secure)
        self.assertEqual(response_detail.status_code, status.HTTP_404_NOT_FOUND)

    def test_project_creation_scoped_correctly(self):
        """
        Ensure project creation automatically binds to the requested workspace organization.
        """
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('project-list', kwargs={'org_slug': self.org1.slug})
        payload = {'name': 'New Project', 'description': 'Brand content'}
        response = self.client.post(url, payload)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_proj_id = response.data['id']
        
        # Verify db record organization is Org 1
        new_proj = Project.objects.get(id=new_proj_id)
        self.assertEqual(new_proj.organization, self.org1)

class ValidationAndRateLimitsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='tester', email='tester@viralops.com', password='password123')
        self.org = Organization.objects.create(name='Test Org', slug='test-org')
        self.membership = Membership.objects.create(user=self.user, organization=self.org, role='MEMBER')
        self.proj = Project.objects.create(organization=self.org, name='Test Project')
        
        self.client.force_authenticate(user=self.user)
        self.client.defaults['HTTP_X_ORG_SLUG'] = self.org.slug

    def test_project_name_length_validation(self):
        """
        Verify that creating a project with a name shorter than 3 characters is rejected.
        """
        url = reverse('project-list', kwargs={'org_slug': self.org.slug})
        response = self.client.post(url, {'name': 'ab', 'description': 'too short'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)

    def test_source_input_youtube_url_validation(self):
        """
        Verify invalid YouTube URL schemes are rejected.
        """
        url = reverse('source-list', kwargs={'org_slug': self.org.slug, 'project_id': self.proj.id})
        response = self.client.post(url, {
            'type': 'YOUTUBE',
            'title': 'Test Video',
            'source_url': 'invalid-url-scheme'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('source_url', response.data)

    def test_source_input_file_size_validation(self):
        """
        Verify that file uploads exceeding the 50MB limit are rejected.
        """
        url = reverse('source-list', kwargs={'org_slug': self.org.slug, 'project_id': self.proj.id})
        response = self.client.post(url, {
            'type': 'VIDEO',
            'title': 'Heavy Video',
            'file_name': 'raw_large.mp4',
            'file_size': 60000000 # 60MB (limit is 50MB)
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('file_size', response.data)

    def test_source_input_text_empty_validation(self):
        """
        Verify text-based source creations require content body.
        """
        url = reverse('source-list', kwargs={'org_slug': self.org.slug, 'project_id': self.proj.id})
        response = self.client.post(url, {
            'type': 'ARTICLE',
            'title': 'Empty Article',
            'text_content': '   ' # whitespace
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('text_content', response.data)


class E2ELifecycleTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='e2e_tester', email='e2e@viralops.com', password='password123')
        self.org = Organization.objects.create(name='E2E Org', slug='e2e-org')
        self.membership = Membership.objects.create(user=self.user, organization=self.org, role='MEMBER')
        self.client.force_authenticate(user=self.user)
        self.client.defaults['HTTP_X_ORG_SLUG'] = self.org.slug

    def test_e2e_repurposing_lifecycle(self):
        # 1. Create project
        proj_url = reverse('project-list', kwargs={'org_slug': self.org.slug})
        proj_response = self.client.post(proj_url, {
            'name': 'E2E Repurposing Project',
            'description': 'End to end testing lifecycle'
        })
        self.assertEqual(proj_response.status_code, status.HTTP_201_CREATED)
        project_id = proj_response.data['id']
        
        # Verify AuditLog for project creation
        self.assertTrue(AuditLog.objects.filter(action='PROJECT_CREATE', details__project_id=project_id).exists())

        # 2. Submit Source Input (YouTube URL)
        source_url = reverse('source-list', kwargs={'org_slug': self.org.slug, 'project_id': project_id})
        source_response = self.client.post(source_url, {
            'type': 'YOUTUBE',
            'title': 'Viral Growth Strategies',
            'source_url': 'https://youtube.com/watch?v=12345'
        })
        self.assertEqual(source_response.status_code, status.HTTP_201_CREATED)
        source_id = source_response.data['id']

        # Verify AuditLog for source submission
        self.assertTrue(AuditLog.objects.filter(action='SOURCE_SUBMIT', details__source_id=source_id).exists())

        # Since CELERY_TASK_ALWAYS_EAGER = True, process_source_input ran synchronously during POST request!
        # Let's verify status of SourceInput.
        source_input = SourceInput.objects.get(id=source_id)
        self.assertEqual(source_input.status, 'COMPLETED')

        # 3. Verify TranscriptRecord was created
        transcript = TranscriptRecord.objects.get(source_input=source_input)
        self.assertIsNotNone(transcript.raw_text)
        self.assertIsNotNone(transcript.normalized_text)
        self.assertTrue(len(transcript.segments) > 0)

        # 4. Verify GeneratedAssets were created under the project
        assets = GeneratedAsset.objects.filter(project_id=project_id)
        self.assertTrue(assets.exists())
        types_created = set(assets.values_list('type', flat=True))
        self.assertIn('HOOK', types_created)
        self.assertIn('TITLE', types_created)
        self.assertIn('CAPTION', types_created)
        self.assertIn('SCRIPT', types_created)

        # 5. Verify UsageEvents were created
        self.assertTrue(UsageEvent.objects.filter(organization=self.org, event_type='TRANSCRIPTION_MINUTES').exists())
        self.assertTrue(UsageEvent.objects.filter(organization=self.org, event_type='AI_GENERATION').exists())

        # 6. Edit one of the generated assets to check save versioning
        asset_to_edit = assets.filter(type='HOOK').first()
        edit_url = reverse('asset-save-version', kwargs={
            'org_slug': self.org.slug,
            'project_id': project_id,
            'pk': asset_to_edit.id
        })
        new_content = "This is a brand new edited hook!"
        edit_response = self.client.post(edit_url, {'content': new_content})
        self.assertEqual(edit_response.status_code, status.HTTP_200_OK)

        # Verify asset content is updated
        asset_to_edit.refresh_from_db()
        self.assertEqual(asset_to_edit.content, new_content)

        # Verify a new version record was saved
        versions = GeneratedAssetVersion.objects.filter(asset=asset_to_edit)
        self.assertEqual(versions.count(), 1)
        self.assertEqual(versions.first().content, new_content)
        self.assertEqual(versions.first().edited_by, self.user)

        # Verify AuditLog for asset edit
        self.assertTrue(AuditLog.objects.filter(action='ASSET_EDITED', details__asset_id=asset_to_edit.id).exists())


