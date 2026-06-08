"""
Content Intelligence Service

Uses the active AI provider to extract structured intelligence from a transcript:
  - summary, topics, keywords, entities, emotional_moments, viral_score

Production: Gemini 2.5 Flash via GeminiProvider
Tests:      Deterministic via MockAIProvider (no network calls)

Saves result to ContentIntelligenceRecord.
"""

import logging

logger = logging.getLogger(__name__)


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
        data = provider.run_content_intelligence(
            project_id=project.id,
            transcript_text=transcript_text,
        )

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
