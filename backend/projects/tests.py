"""
ViralOps Test Suite
===================

AI Isolation: All tests use MockAIProvider via the ai_provider module.
No test makes a real Gemini API call.

Isolation is guaranteed by:
  1. _is_running_tests() detection in ai_provider.get_ai_provider()
  2. Explicit @patch decorators on tests that need to verify provider selection
  3. setUp() calls that inject MockAIProvider via ai_provider.set_provider()
"""

import os
import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch, MagicMock
from rest_framework import status
from rest_framework.test import APIClient

from organizations.models import Organization, Membership
from projects.models import (
    Project, SourceInput, TranscriptRecord, GeneratedAsset,
    GeneratedAssetVersion, AuditLog, UsageEvent,
)
from projects.ai_provider import MockAIProvider, set_provider, reset_provider

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_youtube_transcript():
    """
    Build a transcript long enough to pass TranscriptValidator (>1000 chars).
    Contains no forbidden terms.
    """
    paragraph = (
        "Content creation is the foundation of every successful digital strategy. "
        "Understanding your audience, delivering consistent value, and optimising "
        "for engagement are the three pillars every creator must master. "
        "In this session we explore viral growth frameworks, retention strategies, "
        "and the exact methods top creators use to scale from zero to one million subscribers. "
    )
    return (paragraph * 10).strip()   # ~7000 chars — well above the 1000-char minimum


def _make_youtube_diagnostics(transcript_text):
    """Build a PASS diagnostics dict matching what ingest_youtube_source() produces."""
    from django.utils import timezone
    return {
        "status": "PASS",
        "length": len(transcript_text),
        "source": "youtube",
        "retrieval_method": "youtube-transcript-api/manual-en",
        "retrieval_timestamp": timezone.now().isoformat(),
        "transcript_preview": transcript_text[:500],
        "failures": [],
    }


# ---------------------------------------------------------------------------
# Tenant Separation
# ---------------------------------------------------------------------------

class TenantSeparationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user1 = User.objects.create_user(username='user1', email='user1@viralops.com', password='password123')
        self.org1 = Organization.objects.create(name='Org One', slug='org-one')
        Membership.objects.create(user=self.user1, organization=self.org1, role='MEMBER')

        self.user2 = User.objects.create_user(username='user2', email='user2@viralops.com', password='password123')
        self.org2 = Organization.objects.create(name='Org Two', slug='org-two')
        Membership.objects.create(user=self.user2, organization=self.org2, role='MEMBER')

        self.proj1 = Project.objects.create(organization=self.org1, name='Org 1 Project', description='Secret')
        self.proj2 = Project.objects.create(organization=self.org2, name='Org 2 Project', description='Private')

    def test_tenant_scoping_isolation(self):
        """User 1 cannot see or access Project 2 belonging to Organization 2."""
        self.client.force_authenticate(user=self.user1)
        self.client.defaults['HTTP_X_ORG_SLUG'] = self.org1.slug

        url = reverse('project-list', kwargs={'org_slug': self.org1.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Org 1 Project')

        url_detail = reverse('project-detail', kwargs={'org_slug': self.org1.slug, 'pk': self.proj2.id})
        response_detail = self.client.get(url_detail)
        self.assertEqual(response_detail.status_code, status.HTTP_404_NOT_FOUND)

    def test_project_creation_scoped_correctly(self):
        """Project creation automatically binds to the requested workspace organization."""
        self.client.force_authenticate(user=self.user1)
        url = reverse('project-list', kwargs={'org_slug': self.org1.slug})
        response = self.client.post(url, {'name': 'New Project', 'description': 'Brand content'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_proj = Project.objects.get(id=response.data['id'])
        self.assertEqual(new_proj.organization, self.org1)


# ---------------------------------------------------------------------------
# Validation & Rate Limits
# ---------------------------------------------------------------------------

class ValidationAndRateLimitsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='tester', email='tester@viralops.com', password='password123')
        self.org = Organization.objects.create(name='Test Org', slug='test-org')
        Membership.objects.create(user=self.user, organization=self.org, role='MEMBER')
        self.proj = Project.objects.create(organization=self.org, name='Test Project')
        self.client.force_authenticate(user=self.user)
        self.client.defaults['HTTP_X_ORG_SLUG'] = self.org.slug

    def test_project_name_length_validation(self):
        """Project names shorter than 3 chars are rejected."""
        url = reverse('project-list', kwargs={'org_slug': self.org.slug})
        response = self.client.post(url, {'name': 'ab', 'description': 'too short'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)

    def test_source_input_youtube_url_validation(self):
        """Invalid YouTube URL schemes are rejected."""
        url = reverse('source-list', kwargs={'org_slug': self.org.slug, 'project_id': self.proj.id})
        response = self.client.post(url, {
            'type': 'YOUTUBE',
            'title': 'Test Video',
            'source_url': 'invalid-url-scheme',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('source_url', response.data)

    def test_source_input_file_size_validation(self):
        """File uploads exceeding 50 MB are rejected."""
        url = reverse('source-list', kwargs={'org_slug': self.org.slug, 'project_id': self.proj.id})
        response = self.client.post(url, {
            'type': 'VIDEO',
            'title': 'Heavy Video',
            'file_name': 'raw_large.mp4',
            'file_size': 60_000_000,   # 60 MB > 50 MB limit
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('file_size', response.data)

    def test_source_input_text_empty_validation(self):
        """Text-based sources with only whitespace are rejected."""
        url = reverse('source-list', kwargs={'org_slug': self.org.slug, 'project_id': self.proj.id})
        response = self.client.post(url, {
            'type': 'ARTICLE',
            'title': 'Empty Article',
            'text_content': '   ',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('text_content', response.data)


# ---------------------------------------------------------------------------
# E2E Lifecycle (AI-isolated)
# ---------------------------------------------------------------------------

class E2ELifecycleTestCase(TestCase):
    """
    Full pipeline test — creates project, submits YouTube source, verifies assets.

    AI Isolation:
      - YouTube transcript retrieval is mocked (no youtube-transcript-api call)
      - Asset generation uses MockAIProvider (no Gemini call)
    """

    def setUp(self):
        set_provider(MockAIProvider())   # inject mock before every test
        self.client = APIClient()
        self.user = User.objects.create_user(username='e2e_tester', email='e2e@viralops.com', password='password123')
        self.org = Organization.objects.create(name='E2E Org', slug='e2e-org')
        Membership.objects.create(user=self.user, organization=self.org, role='MEMBER')
        self.client.force_authenticate(user=self.user)
        self.client.defaults['HTTP_X_ORG_SLUG'] = self.org.slug

    def tearDown(self):
        reset_provider()

    @patch('projects.services.youtube_ingestion.ingest_youtube_source')
    def test_e2e_repurposing_lifecycle(self, mock_ingest):
        """
        Full repurposing lifecycle:
          project create → source submit → pipeline → assets → edit → version
        """
        transcript_text = _make_mock_youtube_transcript()

        # Mock the YouTube ingestion layer — return PASS diagnostics
        def _fake_ingest(source_input):
            from django.utils import timezone
            source_input.text_content = transcript_text
            source_input.transcript_source = 'youtube'
            source_input.transcript_length = len(transcript_text)
            source_input.transcript_validation_status = 'PASS'
            source_input.transcript_retrieval_method = 'youtube-transcript-api/manual-en'
            source_input.transcript_retrieved_at = timezone.now()
            source_input.transcript_preview = transcript_text[:500]
            source_input.save(update_fields=[
                'text_content', 'transcript_source', 'transcript_length',
                'transcript_validation_status', 'transcript_retrieval_method',
                'transcript_retrieved_at', 'transcript_preview',
            ])
            return _make_youtube_diagnostics(transcript_text)

        mock_ingest.side_effect = _fake_ingest

        # 1. Create project
        proj_url = reverse('project-list', kwargs={'org_slug': self.org.slug})
        proj_response = self.client.post(proj_url, {
            'name': 'E2E Repurposing Project',
            'description': 'End to end testing lifecycle',
        })
        self.assertEqual(proj_response.status_code, status.HTTP_201_CREATED)
        project_id = proj_response.data['id']

        # Verify AuditLog for project creation
        self.assertTrue(
            AuditLog.objects.filter(action='PROJECT_CREATE', details__project_id=project_id).exists()
        )

        # 2. Submit Source Input (YouTube URL)
        source_url = reverse('source-list', kwargs={'org_slug': self.org.slug, 'project_id': project_id})
        source_response = self.client.post(source_url, {
            'type': 'YOUTUBE',
            'title': 'Viral Growth Strategies',
            'source_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        })
        self.assertEqual(source_response.status_code, status.HTTP_201_CREATED)
        source_id = source_response.data['id']

        # Verify AuditLog for source submission
        self.assertTrue(
            AuditLog.objects.filter(action='SOURCE_SUBMIT', details__source_id=source_id).exists()
        )

        # CELERY_TASK_ALWAYS_EAGER=True → pipeline ran synchronously
        source_input = SourceInput.objects.get(id=source_id)
        self.assertEqual(source_input.status, 'COMPLETED')

        # 3. Verify TranscriptRecord
        transcript = TranscriptRecord.objects.get(source_input=source_input)
        self.assertIsNotNone(transcript.raw_text)
        self.assertTrue(len(transcript.normalized_text) > 0)
        self.assertTrue(len(transcript.segments) > 0)

        # 4. Verify GeneratedAssets
        assets = GeneratedAsset.objects.filter(project_id=project_id)
        self.assertTrue(assets.exists())
        types_created = set(assets.values_list('type', flat=True))
        self.assertIn('HOOK', types_created)
        self.assertIn('TITLE', types_created)
        self.assertIn('CAPTION', types_created)
        self.assertIn('SCRIPT', types_created)

        # Verify mock content was used (deterministic)
        hook_asset = assets.filter(type='HOOK').first()
        self.assertIn("Hook", hook_asset.content)

        # 5. Verify UsageEvents
        self.assertTrue(
            UsageEvent.objects.filter(organization=self.org, event_type='TRANSCRIPTION_MINUTES').exists()
        )
        self.assertTrue(
            UsageEvent.objects.filter(organization=self.org, event_type='AI_GENERATION').exists()
        )

        # 6. Edit asset — verify versioning
        edit_url = reverse('asset-save-version', kwargs={
            'org_slug': self.org.slug,
            'project_id': project_id,
            'pk': hook_asset.id,
        })
        new_content = "This is a brand new edited hook!"
        edit_response = self.client.post(edit_url, {'content': new_content})
        self.assertEqual(edit_response.status_code, status.HTTP_200_OK)

        hook_asset.refresh_from_db()
        self.assertEqual(hook_asset.content, new_content)

        versions = GeneratedAssetVersion.objects.filter(asset=hook_asset)
        self.assertEqual(versions.count(), 1)
        self.assertEqual(versions.first().content, new_content)
        self.assertEqual(versions.first().edited_by, self.user)

        self.assertTrue(
            AuditLog.objects.filter(action='ASSET_EDITED', details__asset_id=hook_asset.id).exists()
        )


# ---------------------------------------------------------------------------
# File Upload / Storage
# ---------------------------------------------------------------------------

class FileUploadStorageTestCase(TestCase):
    def setUp(self):
        set_provider(MockAIProvider())
        self.client = APIClient()
        self.user = User.objects.create_user(username='file_tester', email='file_tester@viralops.com', password='password123')
        self.org = Organization.objects.create(name='File Org', slug='file-org')
        Membership.objects.create(user=self.user, organization=self.org, role='MEMBER')
        self.proj = Project.objects.create(organization=self.org, name='File Project')
        self.client.force_authenticate(user=self.user)
        self.client.defaults['HTTP_X_ORG_SLUG'] = self.org.slug

    def tearDown(self):
        reset_provider()

    @patch('projects.transcription.services.transcribe_source_input')
    def test_file_upload_valid(self, mock_transcribe):
        """Valid MP4 upload creates source, download URL is accessible."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        # Mock transcription so VIDEO type doesn't need a real audio provider
        mock_transcribe.return_value = (
            'Mock video transcript content for testing.',
            'Mock video transcript content for testing.',
            [{'text': 'Mock video transcript content for testing.', 'start_time': 0.0, 'end_time': 5.0}],
            5.0,
        )

        video_file = SimpleUploadedFile("test_video.mp4", b"fake mp4 video binary content", content_type="video/mp4")

        url = reverse('source-list', kwargs={'org_slug': self.org.slug, 'project_id': self.proj.id})
        response = self.client.post(url, {
            'type': 'VIDEO',
            'title': 'Test Upload',
            'file': video_file,
        }, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('file', response.data)
        self.assertTrue(response.data['file'].endswith('.mp4'))

        source_id = response.data['id']
        download_url = reverse('source-download', kwargs={
            'org_slug': self.org.slug,
            'project_id': self.proj.id,
            'pk': source_id,
        })
        dl_response = self.client.get(download_url)
        self.assertEqual(dl_response.status_code, status.HTTP_200_OK)
        self.assertIn('download_url', dl_response.data)

    def test_file_upload_rejected_over_size(self):
        """Files over 50 MB are rejected at validation."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        large_file = SimpleUploadedFile("too_large.mp4", b"0" * 52_428_801, content_type="video/mp4")

        url = reverse('source-list', kwargs={'org_slug': self.org.slug, 'project_id': self.proj.id})
        response = self.client.post(url, {
            'type': 'VIDEO',
            'title': 'Too Large Upload',
            'file': large_file,
        }, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('file', response.data)

    def test_file_upload_rejected_unsupported_type(self):
        """Executable files are rejected."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        exe_file = SimpleUploadedFile("malware.exe", b"fake binary", content_type="application/octet-stream")

        url = reverse('source-list', kwargs={'org_slug': self.org.slug, 'project_id': self.proj.id})
        response = self.client.post(url, {
            'type': 'VIDEO',
            'title': 'Unsupported Upload',
            'file': exe_file,
        }, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('file', response.data)


# ---------------------------------------------------------------------------
# Transcription
# ---------------------------------------------------------------------------

class TranscriptionTestCase(TestCase):
    def setUp(self):
        set_provider(MockAIProvider())
        self.org = Organization.objects.create(name='Trans Org', slug='trans-org')
        self.user = User.objects.create_user(username='trans_tester', email='trans@viralops.com', password='password123')
        self.proj = Project.objects.create(organization=self.org, name='Trans Project')

    def tearDown(self):
        reset_provider()

    def test_transcription_text_source_direct(self):
        """
        A text-based ARTICLE source with pre-set text_content is returned directly
        (no network call, no transcription provider needed).
        """
        from projects.transcription.services import transcribe_source_input

        os.environ.pop('OPENAI_API_KEY', None)
        os.environ.pop('ASSEMBLYAI_API_KEY', None)

        source = SourceInput.objects.create(
            project=self.proj,
            type='ARTICLE',
            title='Sample Title',
            text_content='Hello world. This is a text content source material.',
        )
        raw, norm, segments, duration = transcribe_source_input(source)
        self.assertEqual(raw, source.text_content)
        self.assertTrue(len(segments) > 0)
        self.assertEqual(segments[0]['text'], 'Hello world. This is a text content source material.')

    @patch('requests.post')
    def test_transcription_whisper_mock(self, mock_post):
        """Whisper provider returns correct segments from mocked API response."""
        from projects.transcription.services import transcribe_source_input
        from django.core.files.uploadedfile import SimpleUploadedFile

        os.environ['OPENAI_API_KEY'] = 'mock_openai_key'
        os.environ['TRANSCRIPTION_PROVIDER'] = 'whisper'

        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'text': 'This is a mock transcribed text from Whisper.',
            'duration': 120.5,
            'segments': [
                {'start': 0.0, 'end': 10.0, 'text': 'This is a mock transcribed text'},
                {'start': 10.0, 'end': 20.0, 'text': 'from Whisper.'},
            ],
        }

        video_file = SimpleUploadedFile("test_video.mp4", b"fake binary", content_type="video/mp4")
        source = SourceInput.objects.create(
            project=self.proj, type='VIDEO', title='Whisper Video', file=video_file
        )

        raw, norm, segments, duration = transcribe_source_input(source)
        self.assertEqual(raw, 'This is a mock transcribed text from Whisper.')
        self.assertEqual(duration, 120)
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0]['text'], 'This is a mock transcribed text')

    @patch('requests.post')
    @patch('requests.get')
    def test_transcription_assemblyai_mock(self, mock_get, mock_post):
        """AssemblyAI provider returns correct segments from mocked API response."""
        from projects.transcription.services import transcribe_source_input
        from django.core.files.uploadedfile import SimpleUploadedFile

        os.environ['ASSEMBLYAI_API_KEY'] = 'mock_assembly_key'
        os.environ['TRANSCRIPTION_PROVIDER'] = 'assemblyai'

        class MockResponse:
            def __init__(self, data, code):
                self.json_data = data
                self.status_code = code
            def json(self):
                return self.json_data
            @property
            def text(self):
                return str(self.json_data)

        mock_post.side_effect = [
            MockResponse({'upload_url': 'https://assemblyai/upload/123'}, 200),
            MockResponse({'id': 'job_123'}, 200),
        ]
        mock_get.return_value = MockResponse({
            'status': 'completed',
            'text': 'This is a mock transcribed text from AssemblyAI.',
            'audio_duration': 65,
            'utterances': [
                {'start': 0, 'end': 5000, 'speaker': 'A', 'text': 'This is a mock transcribed text'},
                {'start': 5000, 'end': 10000, 'speaker': 'B', 'text': 'from AssemblyAI.'},
            ],
        }, 200)

        audio_file = SimpleUploadedFile("test_audio.mp3", b"fake binary", content_type="audio/mp3")
        source = SourceInput.objects.create(
            project=self.proj, type='AUDIO', title='Assembly Audio', file=audio_file
        )

        raw, norm, segments, duration = transcribe_source_input(source)
        self.assertEqual(raw, 'This is a mock transcribed text from AssemblyAI.')
        self.assertEqual(duration, 65)
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0]['speaker'], 'Speaker A')

    def test_usage_logging_minutes(self):
        """125 seconds logs as 2 transcription minutes."""
        from projects.transcription.services import log_transcription_usage
        log_transcription_usage(self.org, self.user, 125)
        usage = UsageEvent.objects.filter(
            organization=self.org, event_type='TRANSCRIPTION_MINUTES'
        ).first()
        self.assertIsNotNone(usage)
        self.assertEqual(usage.quantity, 2)
        self.assertEqual(usage.user, self.user)


# ---------------------------------------------------------------------------
# Observability
# ---------------------------------------------------------------------------

class ObservabilityTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_healthz_endpoint(self):
        response = self.client.get(reverse('healthz'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'status': 'UP'})

    def test_ready_endpoint(self):
        response = self.client.get(reverse('ready'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'READY')

    def test_prometheus_metrics_endpoint(self):
        response = self.client.get('/prometheus/metrics')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('text/plain', response.headers['Content-Type'])
        self.assertIn('viralops_api_requests_total', response.content.decode('utf-8'))


# ---------------------------------------------------------------------------
# Deployment
# ---------------------------------------------------------------------------

class DeploymentTestCase(TestCase):
    @patch('subprocess.run')
    @patch('sys.stdin.isatty', return_value=False)
    def test_deploy_command_migration(self, mock_isatty, mock_run):
        from django.core.management import call_command
        call_command('deploy', stage='migration')
        mock_run.assert_not_called()

    @patch('subprocess.run')
    def test_deploy_command_deploy(self, mock_run):
        from django.core.management import call_command
        call_command('deploy', stage='deploy')
        self.assertTrue(mock_run.called)

    @patch('subprocess.run')
    @patch('django.db.connection.cursor')
    def test_deploy_command_rollback(self, mock_cursor, mock_run):
        from django.core.management import call_command
        mock_cursor.return_value.__enter__.return_value.fetchone.return_value = ('projects', '0001_initial')
        with patch('deploy.management.commands.deploy.call_command') as mock_call:
            call_command('deploy', stage='rollback')
            self.assertTrue(mock_run.called)
            mock_call.assert_any_call('migrate', 'projects', 'zero')

    @patch('projects.smoke_tests.run_smoke_tests', return_value=True)
    def test_deploy_command_smoke(self, mock_smoke):
        from django.core.management import call_command
        call_command('deploy', stage='smoke')
        mock_smoke.assert_called_once()

    @patch('projects.smoke_tests.run_smoke_tests', return_value=True)
    @patch('subprocess.run')
    def test_deploy_command_release_success(self, mock_run, mock_smoke):
        from django.core.management import call_command
        with patch('sys.stdin.isatty', return_value=False):
            call_command('deploy', stage='release')
            self.assertTrue(mock_run.called)
            self.assertTrue(mock_smoke.called)

    @patch('projects.smoke_tests.run_smoke_tests', return_value=False)
    @patch('subprocess.run')
    def test_deploy_command_release_failure_rollback(self, mock_run, mock_smoke):
        from django.core.management import call_command
        from django.core.management.base import CommandError
        with patch('sys.stdin.isatty', return_value=False):
            with patch('deploy.management.commands.deploy.call_command') as mock_call:
                def side_effect(cmd, *args, **kwargs):
                    if kwargs.get('stage') == 'smoke':
                        raise CommandError("Smoke tests failed.")
                    return None
                mock_call.side_effect = side_effect
                with self.assertRaises(CommandError):
                    call_command('deploy', stage='release')
                mock_call.assert_any_call('deploy', stage='rollback', base_url='http://localhost:8000')


# ---------------------------------------------------------------------------
# MFA
# ---------------------------------------------------------------------------

class MFATestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='mfatester',
            email='mfa@viralops.com',
            password='Password123!',
            is_email_verified=True,
        )
        self.client.force_authenticate(user=self.user)

    def test_enable_mfa_success(self):
        response = self.client.post(reverse('auth-mfa-enable'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('secret', response.data)
        self.assertIn('provisioning_uri', response.data)
        self.assertEqual(len(response.data['secret']), 32)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_mfa_enabled)
        self.assertEqual(self.user.mfa_secret, response.data['secret'])

    def test_verify_mfa_success(self):
        from accounts.totp import get_totp_code
        import time
        self.client.post(reverse('auth-mfa-enable'))
        self.user.refresh_from_db()
        code = get_totp_code(self.user.mfa_secret, int(time.time() / 30))
        response = self.client.post(reverse('auth-mfa-verify'), {'code': code})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_mfa_enabled)

    def test_verify_mfa_invalid(self):
        self.client.post(reverse('auth-mfa-enable'))
        response = self.client.post(reverse('auth-mfa-verify'), {'code': '000000'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_mfa_enabled)

    def test_jwt_login_with_mfa(self):
        from accounts.totp import generate_secret, get_totp_code
        import time
        self.user.mfa_secret = generate_secret()
        self.user.is_mfa_enabled = True
        self.user.save()
        self.client.force_authenticate(user=None)

        url = reverse('auth-login')
        response = self.client.post(url, {'username': 'mfatester', 'password': 'Password123!'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.data.get('mfa_required'))

        response = self.client.post(url, {
            'username': 'mfatester', 'password': 'Password123!', 'mfa_token': '000000',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid Multi-Factor Authentication', str(response.data['detail']))

        valid_code = get_totp_code(self.user.mfa_secret, int(time.time() / 30))
        response = self.client.post(url, {
            'username': 'mfatester', 'password': 'Password123!', 'mfa_token': valid_code,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)


# ---------------------------------------------------------------------------
# Ingestion & Social Publish (AI-isolated)
# ---------------------------------------------------------------------------

class IngestionAndSocialPublishTestCase(TestCase):
    """
    Tests for ingestion pipeline and social publishing.

    AI Isolation:
      - YouTube ingestion mocked via patch('projects.services.youtube_ingestion.ingest_youtube_source')
      - Article scraping mocked via patch('requests.get')
      - Asset generation uses MockAIProvider (no Gemini)
    """

    def setUp(self):
        set_provider(MockAIProvider())
        self.client = APIClient()
        self.user = User.objects.create_user(username='prodtester', email='prod@viralops.com', password='password123')
        self.org = Organization.objects.create(name='Prod Org', slug='prod-org')
        Membership.objects.create(user=self.user, organization=self.org, role='MEMBER')
        self.proj = Project.objects.create(organization=self.org, name='Prod Project')
        self.client.force_authenticate(user=self.user)
        self.client.defaults['HTTP_X_ORG_SLUG'] = self.org.slug

    def tearDown(self):
        reset_provider()

    @patch('projects.services.youtube_ingestion.ingest_youtube_source')
    def test_youtube_ingestion_flow(self, mock_ingest):
        """
        YouTube pipeline: mocked transcript retrieval → real segmentation → mock assets.
        Verifies transcript is saved, TranscriptRecord created, assets generated.
        """
        transcript_text = _make_mock_youtube_transcript()

        def _fake_ingest(source_input):
            from django.utils import timezone
            source_input.text_content = transcript_text
            source_input.transcript_source = 'youtube'
            source_input.transcript_length = len(transcript_text)
            source_input.transcript_validation_status = 'PASS'
            source_input.transcript_retrieval_method = 'youtube-transcript-api/manual-en'
            source_input.transcript_retrieved_at = timezone.now()
            source_input.transcript_preview = transcript_text[:500]
            source_input.save(update_fields=[
                'text_content', 'transcript_source', 'transcript_length',
                'transcript_validation_status', 'transcript_retrieval_method',
                'transcript_retrieved_at', 'transcript_preview',
            ])
            return _make_youtube_diagnostics(transcript_text)

        mock_ingest.side_effect = _fake_ingest

        url = reverse('source-list', kwargs={'org_slug': self.org.slug, 'project_id': self.proj.id})
        response = self.client.post(url, {
            'type': 'YOUTUBE',
            'title': 'Engaging Video',
            'source_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        source = SourceInput.objects.get(id=response.data['id'])

        # Verify transcript was stored (not simulated)
        self.assertEqual(source.transcript_validation_status, 'PASS')
        self.assertEqual(source.transcript_source, 'youtube')
        self.assertGreater(source.transcript_length, 1000)
        self.assertNotIn('simulated', (source.text_content or '').lower())

        # Verify TranscriptRecord
        transcript = TranscriptRecord.objects.get(source_input=source)
        self.assertGreater(len(transcript.raw_text), 1000)
        self.assertGreater(len(transcript.segments), 0)

        # Verify assets were generated by mock provider
        assets = GeneratedAsset.objects.filter(project=self.proj)
        self.assertTrue(assets.exists())
        types = set(assets.values_list('type', flat=True))
        self.assertIn('HOOK', types)
        self.assertIn('TITLE', types)

    @patch('projects.transcription.services._extract_article_text')
    def test_article_url_ingestion_flow(self, mock_extract):
        """
        Article ingestion: mocked _extract_article_text → real segmentation → mock assets.
        """
        article_text = (
            "How to Build Viral Content. Content creation requires understanding audience psychology, "
            "distribution channels, and platform algorithms. This guide walks through the proven "
            "frameworks that have helped creators grow from zero to one million subscribers in under "
            "twelve months. The key insight is that virality is not random — it is engineered through "
            "consistent application of hook theory, emotional resonance, and strategic posting cadence. "
            "Every successful creator follows a similar pattern even if they don't realise it. "
            "The most important element is the first three seconds of your video or the first sentence "
            "of your article. If you lose the audience there, nothing else matters. "
        ) * 5   # >500 chars to pass the length check

        mock_extract.return_value = article_text

        url = reverse('source-list', kwargs={'org_slug': self.org.slug, 'project_id': self.proj.id})
        response = self.client.post(url, {
            'type': 'ARTICLE',
            'title': 'Viral Content Guide',
            'source_url': 'https://example.com/viral-content-guide',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        source = SourceInput.objects.get(id=response.data['id'])

        # Verify real article content was scraped (not simulated)
        self.assertIsNotNone(source.text_content)
        self.assertNotIn('simulated content', (source.text_content or '').lower())
        self.assertIn('content', (source.text_content or '').lower())

        # Verify TranscriptRecord
        transcript = TranscriptRecord.objects.get(source_input=source)
        self.assertGreater(len(transcript.raw_text), 0)

    def test_pdf_file_ingestion_flow(self):
        """
        PDF ingestion: text_content field passed directly → segmented → mock assets.
        Verifies real text is preserved throughout the pipeline.
        """
        url = reverse('source-list', kwargs={'org_slug': self.org.slug, 'project_id': self.proj.id})
        response = self.client.post(url, {
            'type': 'PDF',
            'title': 'PDF Document',
            'text_content': 'Manual PDF contents inside the document. ' * 30,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        source = SourceInput.objects.get(id=response.data['id'])

        # Verify the real PDF content was used
        self.assertIn('manual pdf contents', (source.text_content or '').lower())
        self.assertNotIn('simulated', (source.text_content or '').lower())

        # Verify pipeline completed and assets were generated
        assets = GeneratedAsset.objects.filter(project=self.proj)
        self.assertTrue(assets.exists())

    def test_social_publish_api(self):
        """Social publish endpoint creates SocialPublishRecord on valid platform."""
        asset = GeneratedAsset.objects.create(
            project=self.proj,
            type='HOOK',
            platform='MULTI',
            content='This is a killer hook about content creation.',
        )

        url = reverse('asset-publish', kwargs={
            'org_slug': self.org.slug,
            'project_id': self.proj.id,
            'pk': asset.id,
        })

        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(url, {'platform': 'FACEBOOK'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(url, {'platform': 'TWITTER'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        from projects.models import SocialPublishRecord
        self.assertEqual(SocialPublishRecord.objects.count(), 1)
        record = SocialPublishRecord.objects.first()
        self.assertEqual(record.asset, asset)
        self.assertEqual(record.platform, 'TWITTER')
        self.assertEqual(record.status, 'SUCCESS')
        self.assertIn('x.com', record.published_url)
        self.assertEqual(record.published_by, self.user)


# ---------------------------------------------------------------------------
# AI Provider Isolation Tests
# ---------------------------------------------------------------------------

class AIProviderIsolationTestCase(TestCase):
    """
    Verify that MockAIProvider returns deterministic data
    and that no real Gemini API calls are made during tests.
    """

    def setUp(self):
        set_provider(MockAIProvider())

    def tearDown(self):
        reset_provider()

    def test_mock_provider_returns_hooks(self):
        provider = MockAIProvider()
        result = provider.generate_social_assets(
            title="Test Video",
            source_type="PDF",
            content_text="Some content here.",
        )
        self.assertIn('hooks', result)
        self.assertEqual(len(result['hooks']), 3)
        self.assertIsInstance(result['hooks'][0], str)

    def test_mock_provider_returns_titles(self):
        provider = MockAIProvider()
        result = provider.generate_social_assets(
            title="Test", source_type="PDF", content_text="Content."
        )
        self.assertIn('titles', result)
        self.assertEqual(len(result['titles']), 3)

    def test_mock_provider_returns_captions(self):
        provider = MockAIProvider()
        result = provider.generate_social_assets(
            title="Test", source_type="PDF", content_text="Content."
        )
        self.assertIn('captions', result)
        self.assertEqual(len(result['captions']), 3)

    def test_mock_provider_returns_scripts(self):
        provider = MockAIProvider()
        result = provider.generate_social_assets(
            title="Test", source_type="PDF", content_text="Content."
        )
        self.assertIn('scripts', result)
        self.assertGreaterEqual(len(result['scripts']), 1)

    def test_mock_provider_returns_hashtags(self):
        provider = MockAIProvider()
        result = provider.generate_social_assets(
            title="Test", source_type="PDF", content_text="Content."
        )
        self.assertIn('hashtags', result)
        self.assertGreaterEqual(len(result['hashtags']), 5)

    def test_mock_provider_returns_ctas(self):
        provider = MockAIProvider()
        result = provider.generate_social_assets(
            title="Test", source_type="PDF", content_text="Content."
        )
        self.assertIn('ctas', result)
        self.assertEqual(len(result['ctas']), 3)

    def test_mock_provider_youtube_gate_enforced(self):
        """MockAIProvider still enforces the YouTube gate."""
        from projects.services.transcript_validator import TranscriptValidationError
        provider = MockAIProvider()

        # No diagnostics → should raise
        with self.assertRaises(TranscriptValidationError):
            provider.generate_social_assets(
                title="Test",
                source_type="YOUTUBE",
                content_text="Content.",
                transcript_diagnostics=None,
            )

        # FAIL diagnostics → should raise
        with self.assertRaises(TranscriptValidationError):
            provider.generate_social_assets(
                title="Test",
                source_type="YOUTUBE",
                content_text="Content.",
                transcript_diagnostics={"status": "FAIL", "failures": ["too short"]},
            )

    def test_mock_provider_youtube_gate_passes_with_valid_diagnostics(self):
        """MockAIProvider succeeds when transcript_diagnostics status=PASS."""
        from django.utils import timezone
        provider = MockAIProvider()
        diagnostics = {
            "status": "PASS",
            "length": 5000,
            "source": "youtube",
            "retrieval_method": "youtube-transcript-api/manual-en",
            "retrieval_timestamp": timezone.now().isoformat(),
            "transcript_preview": "content...",
            "failures": [],
        }
        result = provider.generate_social_assets(
            title="Test",
            source_type="YOUTUBE",
            content_text="Content.",
            transcript_diagnostics=diagnostics,
        )
        self.assertIn('hooks', result)

    def test_mock_provider_content_intelligence(self):
        """MockAIProvider returns structured intelligence without network calls."""
        provider = MockAIProvider()
        result = provider.run_content_intelligence(project_id=1, transcript_text="Some text content.")
        self.assertIn('summary', result)
        self.assertIn('topics', result)
        self.assertIn('keywords', result)
        self.assertIn('viral_score', result)
        self.assertIsInstance(result['viral_score'], int)
        self.assertGreaterEqual(result['viral_score'], 0)
        self.assertLessEqual(result['viral_score'], 100)

    def test_mock_provider_detect_moments(self):
        """MockAIProvider returns moment list without network calls."""
        provider = MockAIProvider()
        moments = provider.detect_moments("Some long transcript text content.")
        self.assertIsInstance(moments, list)
        self.assertGreater(len(moments), 0)
        moment = moments[0]
        self.assertIn('title', moment)
        self.assertIn('category', moment)
        self.assertIn('score', moment)
        self.assertIn('excerpt', moment)

    def test_mock_provider_is_deterministic(self):
        """Same input always produces identical output."""
        provider = MockAIProvider()
        result1 = provider.generate_social_assets("T", "PDF", "Content A")
        result2 = provider.generate_social_assets("Different Title", "PDF", "Completely different content")
        # Output is identical regardless of input (deterministic mock)
        self.assertEqual(result1['hooks'], result2['hooks'])
        self.assertEqual(result1['titles'], result2['titles'])

    def test_no_genai_import_in_mock_path(self):
        """MockAIProvider does not import google.generativeai."""
        import sys
        # Remove genai from modules if present
        genai_mods = [k for k in sys.modules if 'google.generativeai' in k or k == 'genai']
        for mod in genai_mods:
            del sys.modules[mod]

        provider = MockAIProvider()
        # Calling mock methods should NOT re-import genai
        provider.generate_social_assets("T", "PDF", "content")
        provider.run_content_intelligence(1, "content")
        provider.detect_moments("content")

        # genai should still be absent (not re-imported by mock)
        self.assertFalse(
            any('google.generativeai' in k for k in sys.modules),
            "MockAIProvider should not import google.generativeai"
        )
