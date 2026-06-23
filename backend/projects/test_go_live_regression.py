import os
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone
from projects.models import Project, SourceInput, ProcessingJob, GeneratedAsset, Moment, TranscriptRecord
from projects.ai_provider import NvidiaProvider
from projects.tasks import process_source_input

class GoLivePipelineRegressionTestCase(TestCase):
    """Regression tests for key normalization and completion validation."""

    def setUp(self):
        from organizations.models import Organization
        self.org = Organization.objects.create(name="Test Org", slug="test-org")
        self.project = Project.objects.create(name="Test Project", organization=self.org, status="PENDING")
        self.source = SourceInput.objects.create(
            project=self.project,
            source_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            type="YOUTUBE",
            status="PENDING"
        )
        self.job = ProcessingJob.objects.create(project=self.project, source_input=self.source, status="PENDING")

    @patch('requests.post')
    def test_nvidia_key_normalization(self, mock_post):
        """Test that keys like 'moment_id_255' are normalized to '255' in generate_social_assets_batch."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "moment_id_255": {
                                "hooks": ["Hook 1"],
                                "titles": ["Title 1"],
                                "captions": ["Caption 1"],
                                "ctas": ["CTA 1"],
                                "hashtags": ["#tag"],
                                "thumbnail_copy": ["thumbnail"],
                                "scripts": [{"script": "Script 1", "platform": "MULTI"}]
                            }
                        })
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        # Set env variable
        with patch.dict(os.environ, {"NVIDIA_API_KEY": "test-key"}):
            provider = NvidiaProvider()
            result = provider.generate_social_assets_batch(
                title="Test Title",
                source_type="YOUTUBE",
                moments=[{"id": 255, "title": "Moment 1", "content_text": "Text"}],
                transcript_diagnostics={"status": "PASS"}
            )
            self.assertIn("255", result)
            self.assertNotIn("moment_id_255", result)

    @patch('projects.tasks.redis_client', None)
    @patch('projects.transcription.services.transcribe_source_input')
    @patch('projects.services.content_intelligence_service._run_intelligence_with_retry')
    @patch('projects.services.moment_detection_service.detect_moments')
    @patch('projects.tasks.generate_social_assets_batch')
    def test_completion_fails_if_zero_assets_generated(self, mock_assets_batch, mock_detect, mock_intel, mock_transcribe):
        """Assert that process_source_input task fails/raises if zero assets are generated."""
        mock_transcribe.return_value = ("raw", "normalized", [{"start": 0, "end": 10, "text": "seg"}], 10)
        mock_intel.return_value = {"summary": "summary", "viral_score": 50}
        
        # Setup moments
        moment = Moment.objects.create(
            project=self.project,
            source_input=self.source,
            title="Moment 1",
            category="HOOK",
            score=80,
            start_time="0:00",
            end_time="0:10"
        )
        # Mock assets batch call to return empty dict or wrong keys (generating 0 assets)
        mock_assets_batch.return_value = {}

        # The task should raise an exception (ValueError) because asset count is 0
        from projects.tasks import process_source_input
        
        # When always eager, it propagates exceptions. Let's make sure it raises ValueError.
        with self.assertRaises(ValueError):
            process_source_input(self.source.id)

        # Refresh project and verify status is FAILED, not COMPLETED
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, "FAILED")
        
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, "FAILED")
        self.assertIn("Asset generation failed: 0 assets generated", self.job.error_log)
