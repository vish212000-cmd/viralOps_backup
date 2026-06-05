import time
import json
import logging
import redis
from celery import shared_task
from django.utils import timezone
from django.conf import settings
from .models import (
    SourceInput, Project, ProcessingJob, TranscriptRecord,
    GeneratedAsset, GeneratedAssetVersion, MemoryRecord, UsageEvent
)
from .ai_service import generate_social_assets

logger = logging.getLogger(__name__)

# Initialize Redis client for circuit breaker
try:
    redis_client = redis.Redis.from_url(getattr(settings, 'CELERY_BROKER_URL', 'redis://redis:6379/0'))
except Exception as e:
    logger.warning(f"Could not connect to Redis for circuit breaker: {str(e)}")
    redis_client = None

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_source_input(self, source_input_id):
    """
    Ingest long-form source, validate content, run AI generation, and save outputs.

    For YOUTUBE sources: transcript validation is enforced. If real transcript
    cannot be retrieved, processing stops immediately and FAILED status is set.
    Gemini is NEVER called with unvalidated transcript data.
    """
    task_name = self.name
    if redis_client:
        try:
            if redis_client.get(f"cb_tripped:{task_name}"):
                logger.error(f"[CIRCUIT BREAKER] Task {task_name} aborted because the circuit is OPEN.")
                try:
                    source_input = SourceInput.objects.get(id=source_input_id)
                    source_input.status = 'FAILED'
                    source_input.error_message = "Circuit Breaker is open. AI pipelines are temporarily suspended."
                    source_input.save()
                    job, _ = ProcessingJob.objects.get_or_create(source_input=source_input, project=source_input.project)
                    job.status = 'FAILED'
                    job.error_log = "Circuit Breaker is open. Background processing suspended."
                    job.save()
                except Exception:
                    pass
                return
        except Exception as e:
            logger.warning(f"Failed to check circuit breaker: {str(e)}")

    try:
        source_input = SourceInput.objects.get(id=source_input_id)
    except SourceInput.DoesNotExist:
        logger.error(f"SourceInput {source_input_id} not found.")
        return

    # Initialize or fetch the processing job
    job, created = ProcessingJob.objects.get_or_create(
        source_input=source_input,
        project=source_input.project,
        defaults={'status': 'RUNNING'}
    )
    if not created:
        job.status = 'RUNNING'
        job.save()

    source_input.status = 'PROCESSING'
    source_input.save()

    try:
        logger.info(f"Ingesting source input: {source_input.type} (ID: {source_input.id})")
        time.sleep(2)  # Brief delay for realistic UI loading states

        # 1. Transcribe / ingest content
        from projects.transcription.services import transcribe_source_input
        raw_text, normalized_text, segments, duration_seconds = transcribe_source_input(source_input)

        # Save TranscriptRecord
        TranscriptRecord.objects.update_or_create(
            source_input=source_input,
            defaults={
                'raw_text': raw_text,
                'normalized_text': normalized_text,
                'segments': segments,
            }
        )

        # 2. Build transcript diagnostics for Gemini gate
        transcript_diagnostics = None
        if source_input.type == 'YOUTUBE':
            # Reload to get fields saved by ingest_youtube_source
            source_input.refresh_from_db()
            transcript_diagnostics = {
                "status": source_input.transcript_validation_status or "FAIL",
                "length": source_input.transcript_length or 0,
                "source": source_input.transcript_source or "youtube",
                "retrieval_method": source_input.transcript_retrieval_method or "",
                "retrieval_timestamp": (
                    source_input.transcript_retrieved_at.isoformat()
                    if source_input.transcript_retrieved_at else None
                ),
                "transcript_preview": source_input.transcript_preview or "",
                "failures": [],
            }
            logger.info(
                f"[Task] YouTube transcript diagnostics: "
                f"status={transcript_diagnostics['status']}, "
                f"length={transcript_diagnostics['length']}, "
                f"method={transcript_diagnostics['retrieval_method']}"
            )

        # 3. Get Workspace Memory and Preferences
        org = source_input.project.organization
        memories = {}
        for mem in MemoryRecord.objects.filter(organization=org):
            memories[mem.key] = mem.value

        # 4. Call AI Service (with Gemini gate for YouTube)
        assets_data = generate_social_assets(
            title=source_input.title or source_input.file_name or "Social Asset",
            source_type=source_input.type,
            content_text=normalized_text,
            memory_settings=memories,
            transcript_diagnostics=transcript_diagnostics,
        )

        # 5. Save Generated Assets
        project = source_input.project

        for i, hook in enumerate(assets_data.get('hooks', [])):
            GeneratedAsset.objects.create(
                project=project, type='HOOK', platform='MULTI',
                content=hook, metadata={'index': i}
            )

        for i, title in enumerate(assets_data.get('titles', [])):
            GeneratedAsset.objects.create(
                project=project, type='TITLE', platform='MULTI',
                content=title, metadata={'index': i}
            )

        for i, cap in enumerate(assets_data.get('captions', [])):
            GeneratedAsset.objects.create(
                project=project, type='CAPTION', platform='MULTI',
                content=cap, metadata={'index': i}
            )

        for i, cta in enumerate(assets_data.get('ctas', [])):
            GeneratedAsset.objects.create(
                project=project, type='CTA', platform='MULTI',
                content=cta, metadata={'index': i}
            )

        GeneratedAsset.objects.create(
            project=project, type='HASHTAG', platform='MULTI',
            content=" ".join(assets_data.get('hashtags', []))
        )

        for i, text in enumerate(assets_data.get('thumbnail_copy', [])):
            GeneratedAsset.objects.create(
                project=project, type='THUMBNAIL', platform='MULTI',
                content=text, metadata={'index': i}
            )

        for i, script_obj in enumerate(assets_data.get('scripts', [])):
            GeneratedAsset.objects.create(
                project=project, type='SCRIPT',
                platform=script_obj.get('platform', 'MULTI'),
                content=script_obj.get('script', '')
            )

        GeneratedAsset.objects.create(
            project=project, type='PLATFORM_PACK', platform='MULTI',
            content=json.dumps(assets_data)
        )

        # 6. Usage Logging
        from projects.transcription.services import log_transcription_usage
        log_transcription_usage(org, None, duration_seconds)
        UsageEvent.objects.create(
            organization=org, event_type='AI_GENERATION', quantity=1
        )

        # Reset failures on success
        if redis_client:
            try:
                redis_client.delete(f"cb_failures:{task_name}")
            except Exception:
                pass

        # Complete job
        job.status = 'COMPLETED'
        job.save()

        source_input.status = 'COMPLETED'
        source_input.save()

        project.status = 'COMPLETED'
        project.save()

        logger.info(f"Ingestion job completed successfully for SourceInput: {source_input.id}")

    except Exception as e:
        logger.exception(f"Ingestion job failed for SourceInput {source_input_id}: {e}")
        source_input.status = 'FAILED'
        source_input.error_message = str(e)
        source_input.save()

        job.status = 'FAILED'
        job.error_log = str(e)
        job.save()

        # Update circuit breaker failures
        if redis_client:
            try:
                failures = redis_client.incr(f"cb_failures:{task_name}")
                redis_client.expire(f"cb_failures:{task_name}", 3600)
                if failures >= 5:
                    redis_client.setex(f"cb_tripped:{task_name}", 300, "True")
                    redis_client.delete(f"cb_failures:{task_name}")
                    logger.critical(
                        f"[CIRCUIT BREAKER] Tripped! {task_name} has failed 5 times consecutively."
                    )
            except Exception as re:
                logger.warning(f"Failed to update circuit breaker on failure: {str(re)}")

        raise self.retry(exc=e)


def regenerate_single_asset(asset_id):
    """Regenerates a single asset inline via Gemini (no mock)."""
    try:
        asset = GeneratedAsset.objects.get(id=asset_id)
        source = asset.project.sources.first()
        if not source or not source.text_content:
            raise ValueError("No source content available for regeneration")

        assets_data = generate_social_assets(
            title=source.title or "Content",
            source_type=source.type,
            content_text=source.text_content[:8000],
        )

        type_map = {
            'HOOK': 'hooks',
            'TITLE': 'titles',
            'CAPTION': 'captions',
            'CTA': 'ctas',
            'SCRIPT': 'scripts',
        }
        key = type_map.get(asset.type)
        if key and assets_data.get(key):
            items = assets_data[key]
            new_content = items[0] if isinstance(items[0], str) else items[0].get('script', str(items[0]))
            asset.content = new_content
            asset.save()
            GeneratedAssetVersion.objects.create(
                asset=asset, content=asset.content, edited_by=None
            )
    except Exception as e:
        logger.error(f"Asset regeneration failed: {str(e)}")
