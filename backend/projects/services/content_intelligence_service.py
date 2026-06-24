"""
Content Intelligence Service

Uses the active AI provider to extract structured intelligence from a transcript:
  - summary, topics, keywords, entities, emotional_moments, viral_score

Production: Gemini 2.5 Flash via GeminiProvider
Tests:      Deterministic via MockAIProvider (no network calls)

Saves result to ContentIntelligenceRecord.
"""

import logging
from tenacity import retry, stop_after_attempt

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), reraise=True)
def _run_intelligence_with_retry(provider, project_id, transcript_text):
    return provider.run_content_intelligence(
        project_id=project_id,
        transcript_text=transcript_text,
    )


def run_content_intelligence(project, source_input, transcript_text: str) -> dict:
    """
    Analyze transcript_text and extract structured intelligence.
    Saves a ContentIntelligenceRecord and returns the data dict.

    Args:
        project: Project instance
        source_input: SourceInput instance
        transcript_text: The validated real transcript text

    Returns:
        dict with keys: summary, topics, keywords, entities,
                        emotional_moments, viral_score
    """
    from projects.models import ContentIntelligenceRecord
    from projects.ai_provider import get_ai_provider

    if not transcript_text or len(transcript_text) < 100:
        logger.warning(f"[Intelligence] Transcript too short for project {project.id}, skipping.")
        return {}

    provider = get_ai_provider()

    try:
        import os
        if os.getenv('E2E_MOCK') == '1':
            data = {
                'summary': 'This is a mock summary for E2E.',
                'topics': ['Mock Topic 1', 'Mock Topic 2'],
                'keywords': ['mock', 'e2e', 'test'],
                'entities': ['Mock Entity'],
                'emotional_moments': ['Mock Emotion'],
                'viral_score': 88
            }
        else:
            data = _run_intelligence_with_retry(provider, project.id, transcript_text)

        if not data:
            return {}

        viral_score = max(0, min(100, int(data.get('viral_score', 50))))

        record, _ = ContentIntelligenceRecord.objects.update_or_create(
            project=project,
            defaults={
                'source_input': source_input,
                'summary': data.get('summary', ''),
                'topics': data.get('topics', []),
                'keywords': data.get('keywords', []),
                'entities': data.get('entities', []),
                'emotional_moments': data.get('emotional_moments', []),
                'viral_score': viral_score,
            }
        )

        logger.info(
            f"[Intelligence] Project {project.id}: "
            f"topics={len(record.topics)}, keywords={len(record.keywords)}, "
            f"viral_score={viral_score}"
        )

        return {
            'summary': record.summary,
            'topics': record.topics,
            'keywords': record.keywords,
            'entities': record.entities,
            'emotional_moments': record.emotional_moments,
            'viral_score': record.viral_score,
        }

    except Exception as e:
        logger.error(f"[Intelligence] Failed for project {project.id}: {e}")
        return {}
