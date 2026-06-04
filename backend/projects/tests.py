from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch
import os
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


class FileUploadStorageTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='file_tester', email='file_tester@viralops.com', password='password123')
        self.org = Organization.objects.create(name='File Org', slug='file-org')
        self.membership = Membership.objects.create(user=self.user, organization=self.org, role='MEMBER')
        self.proj = Project.objects.create(organization=self.org, name='File Project')
        
        self.client.force_authenticate(user=self.user)
        self.client.defaults['HTTP_X_ORG_SLUG'] = self.org.slug

    def test_file_upload_valid(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        video_file = SimpleUploadedFile("test_video.mp4", b"fake mp4 video binary content", content_type="video/mp4")
        
        url = reverse('source-list', kwargs={'org_slug': self.org.slug, 'project_id': self.proj.id})
        response = self.client.post(url, {
            'type': 'VIDEO',
            'title': 'Test Upload',
            'file': video_file
        }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('file', response.data)
        self.assertTrue(response.data['file'].endswith('.mp4'))
        
        # Verify signed URL / download endpoint
        source_id = response.data['id']
        download_url = reverse('source-download', kwargs={
            'org_slug': self.org.slug,
            'project_id': self.proj.id,
            'pk': source_id
        })
        dl_response = self.client.get(download_url)
        self.assertEqual(dl_response.status_code, status.HTTP_200_OK)
        self.assertIn('download_url', dl_response.data)

    def test_file_upload_rejected_over_size(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        # Over 50MB file size limit (52428801 bytes)
        large_file = SimpleUploadedFile("too_large.mp4", b"0" * 52428801, content_type="video/mp4")
        
        url = reverse('source-list', kwargs={'org_slug': self.org.slug, 'project_id': self.proj.id})
        response = self.client.post(url, {
            'type': 'VIDEO',
            'title': 'Too Large Upload',
            'file': large_file
        }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('file', response.data)

    def test_file_upload_rejected_unsupported_type(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        exe_file = SimpleUploadedFile("malware.exe", b"fake binary", content_type="application/octet-stream")
        
        url = reverse('source-list', kwargs={'org_slug': self.org.slug, 'project_id': self.proj.id})
        response = self.client.post(url, {
            'type': 'VIDEO',
            'title': 'Unsupported Upload',
            'file': exe_file
        }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('file', response.data)


class TranscriptionTestCase(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Trans Org', slug='trans-org')
        self.user = User.objects.create_user(username='trans_tester', email='trans@viralops.com', password='password123')
        self.proj = Project.objects.create(organization=self.org, name='Trans Project')
        
    def test_transcription_fallback_simulated(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from projects.transcription.services import transcribe_source_input
        
        # Ensure env keys are not present
        os.environ.pop('OPENAI_API_KEY', None)
        os.environ.pop('ASSEMBLYAI_API_KEY', None)
        
        source = SourceInput.objects.create(
            project=self.proj,
            type='ARTICLE',
            title='Sample Title',
            text_content='Hello world. This is a text content source material.'
        )
        raw, norm, segments, duration = transcribe_source_input(source)
        self.assertEqual(raw, source.text_content)
        self.assertTrue(len(segments) > 0)
        self.assertEqual(segments[0]['text'], 'Hello world. This is a text content source material.')

    @patch('requests.post')
    def test_transcription_whisper_mock(self, mock_post):
        import os
        from django.core.files.uploadedfile import SimpleUploadedFile
        from projects.transcription.services import transcribe_source_input
        
        os.environ['OPENAI_API_KEY'] = 'mock_openai_key'
        os.environ['TRANSCRIPTION_PROVIDER'] = 'whisper'
        
        # Mock Response
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'text': 'This is a mock transcribed text from Whisper.',
            'duration': 120.5,
            'segments': [
                {'start': 0.0, 'end': 10.0, 'text': 'This is a mock transcribed text'},
                {'start': 10.0, 'end': 20.0, 'text': 'from Whisper.'}
            ]
        }
        
        # Source input with a mock file
        video_file = SimpleUploadedFile("test_video.mp4", b"fake binary", content_type="video/mp4")
        source = SourceInput.objects.create(
            project=self.proj,
            type='VIDEO',
            title='Whisper Video',
            file=video_file
        )
        
        raw, norm, segments, duration = transcribe_source_input(source)
        self.assertEqual(raw, 'This is a mock transcribed text from Whisper.')
        self.assertEqual(duration, 120)
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0]['text'], 'This is a mock transcribed text')

    @patch('requests.post')
    @patch('requests.get')
    def test_transcription_assemblyai_mock(self, mock_get, mock_post):
        import os
        from django.core.files.uploadedfile import SimpleUploadedFile
        from projects.transcription.services import transcribe_source_input
        
        os.environ['ASSEMBLYAI_API_KEY'] = 'mock_assembly_key'
        os.environ['TRANSCRIPTION_PROVIDER'] = 'assemblyai'
        
        # Mock Upload response & Transcription submission response
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
            def json(self):
                return self.json_data
            @property
            def text(self):
                return str(self.json_data)
        
        mock_post.side_effect = [
            MockResponse({'upload_url': 'https://assemblyai/upload/123'}, 200), # upload
            MockResponse({'id': 'job_123'}, 200) # submit job
        ]
        
        # Mock polling response
        mock_get.return_value = MockResponse({
            'status': 'completed',
            'text': 'This is a mock transcribed text from AssemblyAI.',
            'audio_duration': 65, # duration in seconds
            'utterances': [
                {'start': 0, 'end': 5000, 'speaker': 'A', 'text': 'This is a mock transcribed text'},
                {'start': 5000, 'end': 10000, 'speaker': 'B', 'text': 'from AssemblyAI.'}
            ]
        }, 200)
        
        video_file = SimpleUploadedFile("test_audio.mp3", b"fake binary", content_type="audio/mp3")
        source = SourceInput.objects.create(
            project=self.proj,
            type='AUDIO',
            title='Assembly Audio',
            file=video_file
        )
        
        raw, norm, segments, duration = transcribe_source_input(source)
        self.assertEqual(raw, 'This is a mock transcribed text from AssemblyAI.')
        self.assertEqual(duration, 65)
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0]['speaker'], 'Speaker A')

    def test_usage_logging_minutes(self):
        from projects.transcription.services import log_transcription_usage
        
        # 125 seconds = 2 minutes (rounded up/down: max(1, duration/60))
        log_transcription_usage(self.org, self.user, 125)
        
        usage = UsageEvent.objects.filter(organization=self.org, event_type='TRANSCRIPTION_MINUTES').first()
        self.assertIsNotNone(usage)
        self.assertEqual(usage.quantity, 2)
        self.assertEqual(usage.user, self.user)


class ObservabilityTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_healthz_endpoint(self):
        url = reverse('healthz')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'status': 'UP'})

    def test_ready_endpoint(self):
        url = reverse('ready')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'READY')

    def test_prometheus_metrics_endpoint(self):
        # prometheus endpoint is exposed under root prometheus/metrics
        response = self.client.get('/prometheus/metrics')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify it returns plain text format expected by Prometheus
        self.assertIn('text/plain', response.headers['Content-Type'])
        self.assertIn('viralops_api_requests_total', response.content.decode('utf-8'))





