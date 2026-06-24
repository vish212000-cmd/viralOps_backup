import time
import json
import logging
import redis
from celery import shared_task
from django.utils import timezone
from django.conf import settings
from .models import (
    SourceInput, Project, ProcessingJob, TranscriptRecord, TranscriptSegment,
    GeneratedAsset, GeneratedAssetVersion, MemoryRecord, UsageEvent, Moment,
)
from .ai_service import generate_social_assets, generate_social_assets_batch

logger = logging.getLogger(__name__)

try:
    redis_client = redis.Redis.from_url(
        getattr(settings, 'CELERY_BROKER_URL', 'redis://redis:6379/0')
    )
except Exception as e:
    logger.warning(f"Could not connect to Redis for circuit breaker: {str(e)}")
    redis_client = None

def is_ai_quota_error(e):
    err_str = str(e).lower()
    return (
        "429" in err_str or
        "quota" in err_str or
        "rate limit" in err_str or
        "unavailable" in err_str or
        type(e).__name__ in ["ResourceExhausted", "TooManyRequests", "ServiceUnavailable"]
    )

def _save_assets(project, assets_data, moment=None):
    """Persist generated assets to the database."""
    if not isinstance(assets_data, dict):
        logger.error(f"Invalid asset payload format: expected dict, got {type(assets_data)}")
        return

    hooks = assets_data.get('hooks')
    if not isinstance(hooks, list):
        hooks = []
    for i, hook in enumerate(hooks):
        GeneratedAsset.objects.create(
            project=project, type='HOOK', platform='MULTI',
            content=hook, metadata={'index': i}, moment=moment
        )

    titles = assets_data.get('titles')
    if not isinstance(titles, list):
        titles = []
    for i, title in enumerate(titles):
        GeneratedAsset.objects.create(
            project=project, type='TITLE', platform='MULTI',
            content=title, metadata={'index': i}, moment=moment
        )

    captions = assets_data.get('captions')
    if not isinstance(captions, list):
        captions = []
    for i, cap in enumerate(captions):
        GeneratedAsset.objects.create(
            project=project, type='CAPTION', platform='MULTI',
            content=cap, metadata={'index': i}, moment=moment
        )

    ctas = assets_data.get('ctas')
    if not isinstance(ctas, list):
        ctas = []
    for i, cta in enumerate(ctas):
        GeneratedAsset.objects.create(
            project=project, type='CTA', platform='MULTI',
            content=cta, metadata={'index': i}, moment=moment
        )

    hashtags = assets_data.get('hashtags')
    if not isinstance(hashtags, list):
        hashtags = []
    hashtag_text = " ".join(hashtags)
    if hashtag_text:
        GeneratedAsset.objects.create(
            project=project, type='HASHTAG', platform='MULTI',
            content=hashtag_text, moment=moment
        )

    thumbnail_copy = assets_data.get('thumbnail_copy')
    if not isinstance(thumbnail_copy, list):
        thumbnail_copy = []
    for i, text in enumerate(thumbnail_copy):
        GeneratedAsset.objects.create(
            project=project, type='THUMBNAIL', platform='MULTI',
            content=text, metadata={'index': i}, moment=moment
        )

    scripts = assets_data.get('scripts')
    if not isinstance(scripts, list):
        scripts = []
    for script_obj in scripts:
        if isinstance(script_obj, dict):
            script_content = script_obj.get('script', '')
            script_platform = script_obj.get('platform', 'MULTI')
        else:
            script_content = str(script_obj)
            script_platform = 'MULTI'
        GeneratedAsset.objects.create(
            project=project, type='SCRIPT', platform=script_platform,
            content=script_content, moment=moment
        )
    GeneratedAsset.objects.create(
        project=project, type='PLATFORM_PACK', platform='MULTI',
        content=json.dumps(assets_data), moment=moment
    )


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_source_input(self, source_input_id):
    """
    Full ingestion + intelligence pipeline:

      Step 1: Transcription — extract raw text and segments
      Step 2: YouTube transcript gate — enforce validation for YouTube sources
      Step 3: Content Intelligence — topics, keywords, summary via Gemini
      Step 4: Moment Detection + Scoring — detect and rank moments via Gemini
      Step 5: Asset Generation — generate social assets for top moments

    Non-fatal steps (3, 4) log warnings on failure but do not abort the pipeline.
    Fatal steps (1, 2, 5) will mark the job FAILED and trigger retry.
    """
    task_name = self.name

    # ── Circuit Breaker Check ─────────────────────────────────────────────────
    if redis_client:
        try:
            if redis_client.get(f"cb_tripped:{task_name}"):
                logger.error(f"[CIRCUIT BREAKER] Task {task_name} aborted — circuit is OPEN.")
                try:
                    source_input = SourceInput.objects.get(id=source_input_id)
                    source_input.status = 'FAILED'
                    source_input.error_message = "Circuit Breaker is open. Pipelines temporarily suspended."
                    source_input.save()
                    job, _ = ProcessingJob.objects.get_or_create(
                        source_input=source_input, project=source_input.project
                    )
                    job.status = 'FAILED'
                    job.error_log = "Circuit Breaker is open."
                    job.save()
                except Exception:
                    pass
                return
        except Exception as e:
            logger.warning(f"Failed to check circuit breaker: {str(e)}")

    # ── Load source_input ─────────────────────────────────────────────────────
    try:
        source_input = SourceInput.objects.get(id=source_input_id)
    except SourceInput.DoesNotExist:
        logger.error(f"SourceInput {source_input_id} not found.")
        return

    project = source_input.project  # ← assigned here, used throughout

    job, created = ProcessingJob.objects.get_or_create(
        source_input=source_input,
        project=project,
        defaults={'status': 'RUNNING'}
    )
    if not created:
        job.status = 'RUNNING'
        job.save()

    if project.status == 'COMPLETED' and GeneratedAsset.objects.filter(project=project).exists():
        logger.info(f"Project {project.id} is already completed. Skipping process_source_input.")
        job.status = 'COMPLETED'
        job.save()
        return

    source_input.status = 'PROCESSING'
    source_input.save()
    
    project.status = 'PROCESSING'
    project.save()

    lock_key = f"project_ai_generation_{project.id}"
    lock_acquired = False
    if redis_client:
        try:
            lock_acquired = redis_client.set(lock_key, "LOCKED", nx=True, ex=3600)
            if not lock_acquired:
                logger.warning(f"AI generation already running for project {project.id}. Exiting gracefully.")
                return
        except Exception as e:
            logger.warning(f"Failed to acquire Redis lock: {e}")

    current_step = 'Initialization'

    try:
        # ── Step 1: Transcription ─────────────────────────────────────────────
        current_step = 'Transcription'
        logger.info(f"[Task] Step 1/5 — Ingesting {source_input.type} (ID: {source_input.id})")

        from projects.transcription.services import transcribe_source_input as _transcribe
        raw_text, normalized_text, segments, duration_seconds = _transcribe(source_input)

        transcript_record, _ = TranscriptRecord.objects.update_or_create(
            source_input=source_input,
            defaults={
                'raw_text': raw_text,
                'normalized_text': normalized_text,
                'segments': segments,
            }
        )

        # Persist segments to TranscriptSegment table
        TranscriptSegment.objects.filter(transcript_record=transcript_record).delete()
        segment_objs = [
            TranscriptSegment(
                transcript_record=transcript_record,
                start_time=float(seg.get("start", 0.0)),
                end_time=float(seg.get("end", 0.0)),
                speaker=str(seg.get("speaker", "Speaker 1")),
                text=str(seg.get("text", "")),
                segment_index=i,
            )
            for i, seg in enumerate(segments)
        ]
        if segment_objs:
            TranscriptSegment.objects.bulk_create(segment_objs)

        logger.info(
            f"[Task] Step 1/5 ✓ — {len(segments)} segments, {len(normalized_text)} chars"
        )

        # ── Step 2: YouTube Transcript Gate ───────────────────────────────────
        current_step = 'YouTube Transcript Gate'
        transcript_diagnostics = None
        if source_input.type == 'YOUTUBE':
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
                f"[Task] Step 2/5 — YouTube gate: "
                f"status={transcript_diagnostics['status']}, "
                f"length={transcript_diagnostics['length']}"
            )

        # ── Step 3: Content Intelligence (non-fatal) ──────────────────────────
        current_step = 'Content Intelligence'
        logger.info("STEP 2 STARTED: Content Intelligence")
        try:
            from projects.services.content_intelligence_service import run_content_intelligence
            run_content_intelligence(project, source_input, normalized_text)
            logger.info("STEP 2 COMPLETED: Content Intelligence")
        except Exception as intel_err:
            logger.exception("STEP 2 FAILED")
            if is_ai_quota_error(intel_err):
                raise intel_err
            logger.warning(f"[Task] Step 3/5 ⚠ — Content intelligence failed (non-fatal): {intel_err}")

        # ── Step 4: Moment Detection + Scoring (non-fatal) ───────────────────
        current_step = 'Moment Detection'
        logger.info(f"[Task] Step 4/5 — Moment detection + scoring")
        try:
            from projects.services.moment_detection_service import detect_moments
            from projects.services.moment_scoring_service import rescore_moments
            # detect_moments expects (project, source_input, transcript_record: TranscriptRecord)
            detect_moments(project, source_input, transcript_record)
            rescore_moments(project)
            moment_count = Moment.objects.filter(project=project).count()
            logger.info(f"[Task] Step 4/5 ✓ — {moment_count} moments detected and scored")
        except Exception as moment_err:
            if is_ai_quota_error(moment_err):
                raise moment_err
            logger.warning(f"[Task] Step 4/5 ⚠ — Moment detection failed (non-fatal): {moment_err}")

        # ── Step 5: AI Asset Generation ───────────────────────────────────────
        current_step = 'Asset Generation'
        logger.info(f"[Task] Step 5/5 — Generating social assets via Gemini")
        org = project.organization
        memories = {mem.key: mem.value for mem in MemoryRecord.objects.filter(organization=org)}

        top_moments = list(Moment.objects.filter(project=project).order_by('-score')[:5])

        if not top_moments:
            # No moments detected — generate from full transcript
            logger.info("[Task] No moments found — generating from full transcript")
            GeneratedAsset.objects.filter(project=project).delete()
            assets_data = generate_social_assets(
                title=source_input.title or source_input.file_name or "Content",
                source_type=source_input.type,
                content_text=normalized_text,
                memory_settings=memories,
                transcript_diagnostics=transcript_diagnostics,
            )
            _save_assets(project, assets_data, moment=None)
        else:
            # Generate assets for all top moments in ONE batch call
            GeneratedAsset.objects.filter(project=project).delete()
            
            moments_payload = []
            for moment in top_moments:
                moments_payload.append({
                    "id": moment.id,
                    "title": moment.title,
                    "content_text": moment.excerpt if moment.excerpt else normalized_text[:3000]
                })
                
            batch_results = generate_social_assets_batch(
                title=source_input.title or source_input.file_name or 'Content',
                source_type=source_input.type,
                moments=moments_payload,
                memory_settings=memories,
                transcript_diagnostics=transcript_diagnostics,
            )
            
            for moment in top_moments:
                assets_data = batch_results.get(str(moment.id))
                if assets_data:
                    _save_assets(project, assets_data, moment=moment)
                else:
                    logger.warning(f"[Task] Missing batch generated assets for moment {moment.id}. Available keys: {list(batch_results.keys())}")

        logger.info(f"[Task] Step 5/5 ✓ — Asset generation complete")

        # ── Usage Logging ─────────────────────────────────────────────────────
        from projects.transcription.services import log_transcription_usage
        log_transcription_usage(org, None, duration_seconds)
        UsageEvent.objects.create(organization=org, event_type='AI_GENERATION', quantity=1)

        # Reset circuit breaker on success
        if redis_client:
            try:
                redis_client.delete(f"cb_failures:{task_name}")
            except Exception:
                pass

        # Mark everything completed
        asset_count = GeneratedAsset.objects.filter(project=project).count()
        if asset_count == 0:
            raise ValueError("Asset generation failed: 0 assets generated for project.")

        job.status = 'COMPLETED'
        job.save()
        source_input.status = 'COMPLETED'
        source_input.save()
        project.status = 'COMPLETED'
        project.save()

        logger.info(f"[Task] ✓ All 5 steps completed for SourceInput {source_input.id}")

        if redis_client and lock_acquired:
            try:
                redis_client.delete(lock_key)
            except Exception:
                pass

    except Exception as e:
        if 'lock_acquired' in locals() and lock_acquired and redis_client:
            try:
                redis_client.delete(lock_key)
            except Exception:
                pass

        if is_ai_quota_error(e) and current_step in ['Content Intelligence', 'Moment Detection', 'Asset Generation']:
            logger.warning(f"[Task] Quota exceeded during AI phase. Gracefully degrading. SourceInput: {source_input_id}")
            project.status = 'PARTIAL_SUCCESS'
            project.save(update_fields=['status'])
            
            source_input.status = 'PARTIAL_SUCCESS'
            source_input.error_message = "AI enhancement temporarily delayed. Core transcript processing completed successfully."
            source_input.save(update_fields=['status', 'error_message'])
            
            job.status = 'PARTIAL_SUCCESS'
            job.error_message = "AI enhancement temporarily delayed."
            job.save(update_fields=['status', 'error_message'])
            
            # Enqueue background retry
            retry_ai_generation.apply_async(args=[source_input.id], countdown=60)
            return

        logger.exception(f"[Task] Pipeline failed for SourceInput {source_input_id}: {e}")

        
        if is_ai_quota_error(e):
            job.retry_count += 1
            job.last_retry_at = timezone.now()
            
            if job.retry_count <= 3:
                delays = {1: 60, 2: 300, 3: 900}
                delay = delays.get(job.retry_count, 900)
                
                project.status = 'RETRYING'
                project.save(update_fields=['status'])
                
                source_input.status = 'RETRYING'
                source_input.error_message = "AI generation temporarily delayed due to provider quota. Retrying automatically."
                source_input.save(update_fields=['status', 'error_message'])
                
                job.status = 'RETRYING'
                job.error_type = type(e).__name__
                job.error_message = "AI generation temporarily delayed due to provider quota. Retrying automatically."
                job.error_log = str(e)
                job.failing_step = current_step
                job.save(update_fields=['status', 'error_log', 'error_type', 'error_message', 'failing_step', 'retry_count', 'last_retry_at'])
                
                logger.info(f"[Task] Quota exceeded for SourceInput {source_input_id}. Retry {job.retry_count}/3 in {delay}s.")
                
                raise self.retry(exc=e, countdown=delay, max_retries=3)

        project.status = 'FAILED'
        project.save(update_fields=['status'])

        source_input.status = 'FAILED'
        source_input.error_message = str(e)
        source_input.save(update_fields=['status', 'error_message'])

        import traceback
        job.status = 'FAILED'
        job.error_type = type(e).__name__
        job.error_message = str(e)
        job.error_log = traceback.format_exc()
        job.failing_step = current_step
        job.save()

        if redis_client:
            try:
                failures = redis_client.incr(f"cb_failures:{task_name}")
                redis_client.expire(f"cb_failures:{task_name}", 3600)
                if failures >= 5:
                    redis_client.setex(f"cb_tripped:{task_name}", 300, "True")
                    redis_client.delete(f"cb_failures:{task_name}")
                    logger.critical(
                        f"[CIRCUIT BREAKER] Tripped! {task_name} failed 5x consecutively."
                    )
            except Exception as cb_err:
                logger.warning(f"Circuit breaker update failed: {str(cb_err)}")

        # For normal (non-quota) errors, preserve original behaviour
        raise self.retry(exc=e)


def regenerate_single_asset(asset_id):
    """Regenerates a single asset via Gemini. No mock fallback."""
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
            'HOOK': 'hooks', 'TITLE': 'titles', 'CAPTION': 'captions',
            'CTA': 'ctas', 'SCRIPT': 'scripts',
        }
        key = type_map.get(asset.type)
        if key and assets_data.get(key):
            items = assets_data[key]
            item = items[0]
            new_content = item if isinstance(item, str) else item.get('script', str(item))
            asset.content = new_content
            asset.save()
            GeneratedAssetVersion.objects.create(asset=asset, content=asset.content, edited_by=None)
    except Exception as e:
        logger.error(f"Asset regeneration failed: {str(e)}")

@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def retry_ai_generation(self, source_input_id):
    """Background task to retry AI asset generation after PARTIAL_SUCCESS degradation."""
    try:
        source_input = SourceInput.objects.get(id=source_input_id)
        project = source_input.project
        transcript_record = source_input.transcript
        normalized_text = transcript_record.normalized_text

        lock_key = f"project_ai_generation_{project.id}"
        lock_acquired = False
        if redis_client:
            try:
                lock_acquired = redis_client.set(lock_key, "LOCKED", nx=True, ex=3600)
                if not lock_acquired:
                    logger.warning(f"AI generation already running for project {project.id}. Exiting gracefully.")
                    return
            except Exception as e:
                logger.warning(f"Failed to acquire Redis lock: {e}")
                
        if project.status == 'COMPLETED' and GeneratedAsset.objects.filter(project=project).exists():
            logger.info(f"Project {project.id} is already completed. Skipping retry_ai_generation.")
            if lock_acquired and redis_client:
                try:
                    redis_client.delete(lock_key)
                except Exception:
                    pass
            return
        
        # We assume Steps 1 and 2 are done. We just run 3, 4, and 5.
        
        # Step 3: Content Intelligence
        try:
            from projects.services.content_intelligence_service import run_content_intelligence
            run_content_intelligence(project, source_input, normalized_text)
        except Exception as intel_err:
            if is_ai_quota_error(intel_err):
                raise intel_err
            logger.warning(f"[Retry Task] Content intelligence failed: {intel_err}")

        # Step 4: Moment Detection
        try:
            from projects.services.moment_detection_service import detect_moments
            from projects.services.moment_scoring_service import rescore_moments
            detect_moments(project, source_input, transcript_record)
            rescore_moments(project)
        except Exception as moment_err:
            if is_ai_quota_error(moment_err):
                raise moment_err
            logger.warning(f"[Retry Task] Moment detection failed: {moment_err}")

        # Step 5: Asset Generation
        org = project.organization
        memories = {mem.key: mem.value for mem in MemoryRecord.objects.filter(organization=org)}
        transcript_diagnostics = {
            "status": source_input.transcript_validation_status or "PASS",
            "length": source_input.transcript_length or 0,
        }
        
        top_moments = list(Moment.objects.filter(project=project).order_by('-score')[:5])
        if not top_moments:
            GeneratedAsset.objects.filter(project=project).delete()
            assets_data = generate_social_assets(
                title=source_input.title or source_input.file_name or "Content",
                source_type=source_input.type,
                content_text=normalized_text,
                memory_settings=memories,
                transcript_diagnostics=transcript_diagnostics,
            )
            _save_assets(project, assets_data, moment=None)
        else:
            GeneratedAsset.objects.filter(project=project).delete()
            
            moments_payload = []
            for moment in top_moments:
                moments_payload.append({
                    "id": moment.id,
                    "title": moment.title,
                    "content_text": moment.excerpt if moment.excerpt else normalized_text[:3000]
                })
                
            batch_results = generate_social_assets_batch(
                title=source_input.title or source_input.file_name or 'Content',
                source_type=source_input.type,
                moments=moments_payload,
                memory_settings=memories,
                transcript_diagnostics=transcript_diagnostics,
            )
            
            for moment in top_moments:
                assets_data = batch_results.get(str(moment.id))
                if assets_data:
                    _save_assets(project, assets_data, moment=moment)
                else:
                    logger.warning(f"[Retry Task] Missing batch generated assets for moment {moment.id}. Available keys: {list(batch_results.keys())}")

        # Mark Success
        asset_count = GeneratedAsset.objects.filter(project=project).count()
        if asset_count == 0:
            raise ValueError("Asset generation failed: 0 assets generated for project.")

        project.status = 'COMPLETED'
        project.save()
        source_input.status = 'COMPLETED'
        source_input.error_message = ''
        source_input.save()
        try:
            job = ProcessingJob.objects.get(source_input=source_input)
            job.status = 'COMPLETED'
            job.error_message = ''
            job.save()
        except ProcessingJob.DoesNotExist:
            pass
        
        if redis_client and lock_acquired:
            try:
                redis_client.delete(lock_key)
            except Exception:
                pass

    except Exception as e:
        if 'lock_acquired' in locals() and lock_acquired and redis_client:
            try:
                redis_client.delete(lock_key)
            except Exception:
                pass

        if is_ai_quota_error(e):
            logger.warning(f"[Retry Task] Quota exceeded on retry {self.request.retries}/3.")
            delays = {1: 300, 2: 900, 3: 3600}
            delay = delays.get(self.request.retries + 1, 3600)
            raise self.retry(exc=e, countdown=delay, max_retries=3)
        else:
            logger.exception(f"[Retry Task] Hard failure: {e}")
            project.status = 'FAILED'
            project.save()
            source_input.status = 'FAILED'
            source_input.error_message = str(e)
            source_input.save()

