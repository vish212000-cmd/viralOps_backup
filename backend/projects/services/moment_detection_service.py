"""
Moment Detection Service

Uses the active AI provider to detect high-value moments in a transcript:
  HOOK, VIRAL, STORY, EMOTIONAL, EDUCATIONAL, CTA

Production: Gemini 2.5 Flash via GeminiProvider
Tests:      Deterministic via MockAIProvider (no network calls)

Saves Moment objects to the database.
"""

import logging

logger = logging.getLogger(__name__)

MOMENT_CATEGORIES = ['HOOK', 'VIRAL', 'STORY', 'EMOTIONAL', 'EDUCATIONAL', 'CTA']


def detect_moments(project, source_input, transcript_record) -> list:
    """
    Detect AI moments from transcript text.
    Saves Moment objects, maps to TranscriptSegments, returns list of moment dicts.

    Args:
        project: Project instance
        source_input: SourceInput instance (can be None)
        transcript_record: TranscriptRecord instance

    Returns:
        list of dicts: [{title, category, score, start_time, end_time, excerpt}]
    """
    from projects.models import Moment, TranscriptSegment
    from projects.ai_provider import get_ai_provider

    transcript_text = transcript_record.normalized_text

    if not transcript_text or len(transcript_text) < 200:
        logger.warning(f"[MomentDetection] Transcript too short for project {project.id}")
        return []

    provider = get_ai_provider()

    try:
        import os
        if os.getenv('E2E_MOCK') == '1':
            moments_data = [
                {'title': 'Mock Hook Moment', 'category': 'HOOK', 'score': 95, 'start_time': '0:00', 'end_time': '0:10', 'excerpt': 'This is a mock excerpt.'},
                {'title': 'Mock Viral Moment', 'category': 'VIRAL', 'score': 85, 'start_time': '0:10', 'end_time': '0:20', 'excerpt': 'This is another mock excerpt.'}
            ]
        else:
            moments_data = provider.detect_moments(transcript_text)
    except Exception as e:
        logger.error(f"[MomentDetection] Provider call failed for project {project.id}: {e}")
        return []

    if not isinstance(moments_data, list):
        logger.error(f"[MomentDetection] Expected list, got {type(moments_data)}")
        return []

    # Clear old moments for this project
    Moment.objects.filter(project=project).delete()

    all_segments = list(
        TranscriptSegment.objects.filter(
            transcript_record=transcript_record
        ).order_by('segment_index')
    )

    def _time_str_to_seconds(t_str) -> float:
        try:
            parts = str(t_str).split(':')
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
            elif len(parts) == 2:
                return int(parts[0]) * 60 + float(parts[1])
            else:
                return float(parts[0])
        except Exception:
            return -1.0

    saved_moments = []
    for m in moments_data:
        category = m.get('category', 'HOOK').upper()
        if category not in MOMENT_CATEGORIES:
            category = 'HOOK'

        score = max(0, min(100, int(m.get('score', 50))))
        start_time_str = str(m.get('start_time', ''))
        end_time_str = str(m.get('end_time', ''))
        start_sec = _time_str_to_seconds(start_time_str)
        end_sec = _time_str_to_seconds(end_time_str)

        moment = Moment.objects.create(
            project=project,
            source_input=source_input,
            title=str(m.get('title', 'Untitled Moment'))[:255],
            category=category,
            score=score,
            start_time=start_time_str,
            end_time=end_time_str,
            excerpt=str(m.get('excerpt', '')),
            metadata={
                'raw_score': score,
                'detection_method': provider.__class__.__name__,
            }
        )

        # Map to overlapping transcript segments
        if all_segments and start_sec >= 0 and end_sec >= 0:
            overlapping = [
                seg for seg in all_segments
                if not (seg.end_time <= start_sec or seg.start_time >= end_sec)
            ]
            if not overlapping:
                # fallback: closest segment by start time
                overlapping = [min(all_segments, key=lambda s: abs(s.start_time - start_sec))]
            moment.segments.set(overlapping)

        saved_moments.append({
            'id': moment.id,
            'title': moment.title,
            'category': moment.category,
            'score': moment.score,
            'start_time': moment.start_time,
            'end_time': moment.end_time,
            'excerpt': moment.excerpt,
        })

    logger.info(
        f"[MomentDetection] Project {project.id}: detected {len(saved_moments)} moments "
        f"via {provider.__class__.__name__}"
    )
    return saved_moments
