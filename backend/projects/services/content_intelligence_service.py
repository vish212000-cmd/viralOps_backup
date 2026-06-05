"""
Content Intelligence Service

Uses Gemini to extract structured intelligence from a transcript:
  - summary (2-3 sentences)
  - topics (list of main themes)
  - keywords (top keywords)
  - entities (people, brands, places)
  - emotional_moments (high-intensity segments)
  - viral_score (0-100)

Saves result to ContentIntelligenceRecord.
"""

import json
import logging
from django.conf import settings
import google.generativeai as genai

logger = logging.getLogger(__name__)

if getattr(settings, 'GEMINI_API_KEY', ''):
    genai.configure(api_key=settings.GEMINI_API_KEY)


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

    if not transcript_text or len(transcript_text) < 100:
        logger.warning(f"[Intelligence] Transcript too short for project {project.id}, skipping.")
        return {}

    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    if not api_key:
        logger.error("[Intelligence] GEMINI_API_KEY not configured.")
        return {}

    prompt = f"""
You are a content intelligence expert. Analyze the following transcript and extract structured data.

Transcript (first 6000 chars):
{transcript_text[:6000]}

Return a single valid JSON object with these exact keys:
{{
  "summary": "2-3 sentence summary of the main content",
  "topics": ["topic1", "topic2", "topic3", "topic4", "topic5"],
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5", "keyword6", "keyword7", "keyword8"],
  "entities": [
    {{"name": "Entity Name", "type": "PERSON|BRAND|PLACE|CONCEPT"}}
  ],
  "emotional_moments": [
    {{"text": "excerpt", "emotion": "excitement|curiosity|inspiration|humor|urgency", "intensity": 0-10}}
  ],
  "viral_score": 75
}}

Rules:
- viral_score: 0-100 based on shareability, hook quality, emotional impact
- topics: 3-6 main themes from the content
- keywords: 6-10 high-value keywords
- entities: max 8 notable people/brands/places mentioned
- emotional_moments: 2-5 highest-intensity segments with short excerpts
- Return only valid JSON, no markdown formatting
"""

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Strip markdown if present
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        data = json.loads(text)

        # Clamp viral_score
        viral_score = max(0, min(100, int(data.get('viral_score', 50))))

        # Upsert ContentIntelligenceRecord
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

    except json.JSONDecodeError as e:
        logger.error(f"[Intelligence] JSON parse error for project {project.id}: {e}")
        return {}
    except Exception as e:
        logger.error(f"[Intelligence] Gemini call failed for project {project.id}: {e}")
        return {}
