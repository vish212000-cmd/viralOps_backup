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
    Ingest long-form source, clean/normalize content,
    run theme/clip detection, run the AI generation pipeline,
    and save the outputs.
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
        time.sleep(2) # Simulate processing/ingestion delay for realistic UI loading states

        # 1. Normalize & transcribe content text
        from projects.transcription.services import transcribe_source_input
        raw_text, normalized_text, segments, duration_seconds = transcribe_source_input(source_input)

        # Save TranscriptRecord
        TranscriptRecord.objects.create(
            source_input=source_input,
            raw_text=raw_text,
            normalized_text=normalized_text,
            segments=segments
        )

        # 2. Get Workspace Memory and Preferences
        org = source_input.project.organization
        memories = {}
        for mem in MemoryRecord.objects.filter(organization=org):
            memories[mem.key] = mem.value

        # 3. Call AI Service
        assets_data = generate_social_assets(
            title=source_input.title or source_input.file_name or "Social Asset",
            source_type=source_input.type,
            content_text=normalized_text,
            memory_settings=memories
        )

        # 4. Save Generated Assets in database
        project = source_input.project
        
        # Save individual assets
        # Hooks
        for i, hook in enumerate(assets_data.get('hooks', [])):
            GeneratedAsset.objects.create(
                project=project,
                type='HOOK',
                platform='MULTI',
                content=hook,
                metadata={'index': i}
            )
            
        # Titles
        for i, title in enumerate(assets_data.get('titles', [])):
            GeneratedAsset.objects.create(
                project=project,
                type='TITLE',
                platform='MULTI',
                content=title,
                metadata={'index': i}
            )
            
        # Captions
        for i, cap in enumerate(assets_data.get('captions', [])):
            GeneratedAsset.objects.create(
                project=project,
                type='CAPTION',
                platform='MULTI',
                content=cap,
                metadata={'index': i}
            )

        # CTAs
        for i, cta in enumerate(assets_data.get('ctas', [])):
            GeneratedAsset.objects.create(
                project=project,
                type='CTA',
                platform='MULTI',
                content=cta,
                metadata={'index': i}
            )

        # Hashtags
        GeneratedAsset.objects.create(
            project=project,
            type='HASHTAG',
            platform='MULTI',
            content=" ".join(assets_data.get('hashtags', []))
        )

        # Thumbnail Copy
        for i, text in enumerate(assets_data.get('thumbnail_copy', [])):
            GeneratedAsset.objects.create(
                project=project,
                type='THUMBNAIL',
                platform='MULTI',
                content=text,
                metadata={'index': i}
            )

        # Scripts
        for i, script_obj in enumerate(assets_data.get('scripts', [])):
            GeneratedAsset.objects.create(
                project=project,
                type='SCRIPT',
                platform=script_obj.get('platform', 'MULTI'),
                content=script_obj.get('script', '')
            )

        # Platform Export Pack (consolidated pack)
        GeneratedAsset.objects.create(
            project=project,
            type='PLATFORM_PACK',
            platform='MULTI',
            content=json.dumps(assets_data)
        )

        # 5. Usage Logging
        from projects.transcription.services import log_transcription_usage
        log_transcription_usage(org, None, duration_seconds)
        UsageEvent.objects.create(
            organization=org,
            event_type='AI_GENERATION',
            quantity=1
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
        logger.exception(f"Ingestion job failed for SourceInput {source_input_id}")
        source_input.status = 'FAILED'
        source_input.error_message = str(e)
        source_input.save()

        job.status = 'FAILED'
        job.error_log = str(e)
        job.save()

        # Update circuit breaker failures and check trigger
        if redis_client:
            try:
                failures = redis_client.incr(f"cb_failures:{task_name}")
                redis_client.expire(f"cb_failures:{task_name}", 3600)
                if failures >= 5:
                    redis_client.setex(f"cb_tripped:{task_name}", 300, "True")
                    redis_client.delete(f"cb_failures:{task_name}")
                    logger.critical(f"[CIRCUIT BREAKER] Tripped! {task_name} has failed 5 times consecutively. Suspending for 5 minutes.")
            except Exception as re:
                logger.warning(f"Failed to update circuit breaker on failure: {str(re)}")

        # Trigger Celery retry policy
        raise self.retry(exc=e)

def regenerate_single_asset(asset_id):
    """
    Regenerates a single asset's content inline.
    """
    try:
        asset = GeneratedAsset.objects.get(id=asset_id)
        # Mock some changes/different options
        if asset.type == 'HOOK':
            asset.content = f"New regenerated hook: Why you are failing at content strategy (fixed version)"
        elif asset.type == 'TITLE':
            asset.content = f"Regenerated: 3 Mistakes You Keep Making on Socials"
        elif asset.type == 'CAPTION':
            asset.content = f"This caption is fully regenerated to drive 10x traffic. Agree or disagree? 👇"
        elif asset.type == 'CTA':
            asset.content = f"Claim your free cheat sheet now (link in bio)!"
        elif asset.type == 'SCRIPT':
            asset.content = f"[Visual: Fast-paced typing] Speaker: Stop wasting time on bad scripts. Do this instead..."
        
        asset.save()
        
        # Save version history
        GeneratedAssetVersion.objects.create(
            asset=asset,
            content=asset.content,
            edited_by=None # System regenerated
        )
    except Exception as e:
        logger.error(f"Asset regeneration failed: {str(e)}")
