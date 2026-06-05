"""
Moment Detection Service

Uses Gemini to detect high-value moments in a transcript:
  - HOOK: compelling opening or attention-grabbing statement
  - VIRAL: shareable, surprising, or highly quotable moment
  - STORY: personal narrative or storytelling arc
  - EMOTIONAL: emotionally resonant segment
  - EDUCATIONAL: key insight, lesson, or fact
  - CTA: natural call-to-action or conversion moment

Each detected moment has:
  title, start_time, end_time, score (0-100), category, transcript_excerpt

Saves Moment objects to the database.
"""

import json
import logging
from django.conf import settings
import google.generativeai as genai

logger = logging.getLogger(__name__)

if getattr(settings, 'GEMINI_API_KEY', ''):
    genai.configure(api_key=settings.GEMINI_API_KEY)


MOMENT_CATEGORIES = ['HOOK', 'VIRAL', 'STORY', 'EMOTIONAL', 'EDUCATIONAL', 'CTA']


def detect_moments(project, source_input, transcript_record) -> list:
    """
    Detect AI moments from transcript text.
    Saves Moment objects, maps to TranscriptSegments, and returns the list of moment dicts.

    Args:
        project: Project instance
        source_input: SourceInput instance (can be None)
        transcript_record: TranscriptRecord instance

    Returns:
        list of dicts: [{title, category, score, start_time, end_time, excerpt}]
    """
    from projects.models import Moment, TranscriptSegment

    transcript_text = transcript_record.normalized_text

    if not transcript_text or len(transcript_text) < 200:
        logger.warning(f"[MomentDetection] Transcript too short for project {project.id}")
        return []

    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    if not api_key:
        logger.error("[MomentDetection] GEMINI_API_KEY not configured.")
        return []

    prompt = f"""
You are an expert viral content strategist and moment detection AI.

Analyze the following transcript and detect the most impactful moments across 6 categories.
For each moment, provide timing estimates based on the position in the transcript.

Transcript:
{transcript_text[:7000]}

Detect 8-15 high-value moments total (mix of categories).

Return a JSON array with this exact structure:
[
  {{
    "title": "Compelling moment title (max 10 words)",
    "category": "HOOK|VIRAL|STORY|EMOTIONAL|EDUCATIONAL|CTA",
    "score": 85,
    "start_time": "0:45",
    "end_time": "1:30",
    "excerpt": "Direct quote or paraphrase from the transcript for this moment (50-120 words)"
  }}
]

Category definitions:
- HOOK: Opening statement or attention-grabbing moment that makes you want to keep watching
- VIRAL: Surprising fact, quotable quote, or shareable insight with high spread potential
- STORY: Personal story, narrative arc, or relatable experience
- EMOTIONAL: Emotionally charged, inspiring, funny, or moving moment
- EDUCATIONAL: Key insight, actionable tip, fact, or lesson that provides real value
- CTA: Natural moment where the speaker directs action (subscribe, buy, try, learn more)

Scoring (0-100):
- 90-100: Exceptional — would stop scrolling immediately
- 70-89: High — strong engagement potential
- 50-69: Good — solid content
- Below 50: Moderate

Rules:
- Detect moments from actual transcript content only
- Mix categories — don't return all of the same type
- Excerpts must be direct quotes or close paraphrases from the transcript
- Return only valid JSON array, no markdown formatting
"""

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        text = response.text.strip()

        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        moments_data = json.loads(text)
        if not isinstance(moments_data, list):
            logger.error(f"[MomentDetection] Expected list, got {type(moments_data)}")
            return []

        # Clear old moments for this project
        Moment.objects.filter(project=project).delete()

        all_segments = list(TranscriptSegment.objects.filter(transcript_record=transcript_record).order_by('segment_index'))

        def _time_str_to_seconds(t_str):
            try:
                parts = str(t_str).split(':')
                if len(parts) == 3:
                    return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
                elif len(parts) == 2:
                    return int(parts[0]) * 60 + float(parts[1])
                else:
                    return float(parts[0])
            except:
                return -1

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
                    'detection_method': 'gemini-2.5-flash',
                }
            )
            
            # Map to segments
            if all_segments and start_sec >= 0 and end_sec >= 0:
                overlapping_segments = [
                    seg for seg in all_segments 
                    if not (seg.end_time <= start_sec or seg.start_time >= end_sec)
                ]
                if not overlapping_segments:
                    # fallback to closest segment
                    closest = min(all_segments, key=lambda s: abs(s.start_time - start_sec))
                    overlapping_segments = [closest]
                moment.segments.set(overlapping_segments)

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
            f"[MomentDetection] Project {project.id}: detected {len(saved_moments)} moments"
        )
        return saved_moments

    except json.JSONDecodeError as e:
        logger.error(f"[MomentDetection] JSON parse error for project {project.id}: {e}")
        return []
    except Exception as e:
        logger.error(f"[MomentDetection] Gemini call failed for project {project.id}: {e}")
        return []
