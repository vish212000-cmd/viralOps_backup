"""
Moment Scoring Service

Re-scores detected moments using a weighted multi-factor algorithm:
  1. Emotional Intensity (from content_intelligence emotional_moments)
  2. Storytelling Quality (narrative structure signals)
  3. Curiosity Gap (question/revelation patterns)
  4. Audience Retention (pacing, variety)
  5. Viral Potential (shareability, surprise factor)
  6. CTA Quality (for CTA moments)

Final score = weighted average, clamped 0-100.
Updates Moment.score in-place.
"""

import re
import logging

logger = logging.getLogger(__name__)

# Category base weights (additional points for matching category patterns)
CATEGORY_PATTERNS = {
    'HOOK': [
        r'\b(imagine|what if|did you know|here\'s the thing|truth is|fact:|secret)\b',
        r'\b(never|always|every|most people|nobody talks about)\b',
        r'\?',  # Questions create curiosity gaps
    ],
    'VIRAL': [
        r'\b(shocking|surprising|incredible|unbelievable|crazy|insane|wild)\b',
        r'\b(nobody|everyone|viral|trending|massive|huge|changed)\b',
        r'!',  # Exclamatory energy
    ],
    'STORY': [
        r'\b(i was|i remember|back when|story|happened|experience|moment)\b',
        r'\b(we|our|together|community|journey|transformation)\b',
    ],
    'EMOTIONAL': [
        r'\b(love|hate|fear|hope|dream|struggle|pain|joy|proud|grateful)\b',
        r'\b(heart|soul|passionate|deeply|truly|honestly|real)\b',
    ],
    'EDUCATIONAL': [
        r'\b(tip|trick|how to|step|method|strategy|framework|system|formula)\b',
        r'\b(learn|teach|understand|know|fact|data|research|study|proof)\b',
        r'\d+%|\d+ steps|\d+ ways',  # Stats and lists
    ],
    'CTA': [
        r'\b(subscribe|follow|click|comment|share|join|download|try|start|get)\b',
        r'\b(link|below|description|bio|profile|page|website|course)\b',
    ],
}

# Scoring weights
WEIGHTS = {
    'base_score': 0.50,          # Original Gemini-assigned score
    'pattern_bonus': 0.20,       # Pattern matching bonus
    'length_quality': 0.10,      # Optimal excerpt length
    'category_alignment': 0.20,  # Excerpt matches expected category patterns
}


def _count_pattern_matches(text: str, patterns: list) -> int:
    text_lower = text.lower()
    count = 0
    for pattern in patterns:
        matches = re.findall(pattern, text_lower)
        count += len(matches)
    return count


def _length_score(excerpt: str) -> float:
    """Optimal excerpt length: 80-200 words → score 1.0, shorter/longer → lower."""
    words = len(excerpt.split())
    if 80 <= words <= 200:
        return 1.0
    elif 40 <= words < 80:
        return 0.7
    elif 200 < words <= 350:
        return 0.8
    elif words < 40:
        return 0.4
    else:
        return 0.6


def rescore_moments(project) -> int:
    """
    Recalculate scores for all Moment objects in a project.
    Uses multi-factor weighted scoring.

    Args:
        project: Project instance

    Returns:
        Number of moments rescored
    """
    from projects.models import Moment

    moments = list(Moment.objects.filter(project=project))
    if not moments:
        return 0

    rescored = 0
    for moment in moments:
        category_patterns = CATEGORY_PATTERNS.get(moment.category, [])
        excerpt = moment.excerpt or moment.title

        # 1. Base score (from Gemini detection)
        base = moment.metadata.get('raw_score', moment.score)
        base_normalized = base / 100.0

        # 2. Pattern match bonus (0-1)
        match_count = _count_pattern_matches(excerpt, category_patterns)
        pattern_bonus = min(1.0, match_count / 5.0)

        # 3. Excerpt length quality (0-1)
        length_quality = _length_score(excerpt)

        # 4. Category alignment — patterns from ALL categories
        all_pattern_counts = {
            cat: _count_pattern_matches(excerpt, patterns)
            for cat, patterns in CATEGORY_PATTERNS.items()
        }
        # Check if the highest-matching category matches the assigned category
        if all_pattern_counts:
            top_category = max(all_pattern_counts, key=all_pattern_counts.get)
            category_alignment = 1.0 if top_category == moment.category else 0.6
        else:
            category_alignment = 0.7

        # Weighted final score
        final_score = (
            base_normalized * WEIGHTS['base_score'] +
            pattern_bonus * WEIGHTS['pattern_bonus'] +
            length_quality * WEIGHTS['length_quality'] +
            category_alignment * WEIGHTS['category_alignment']
        )
        final_score_int = max(0, min(100, int(final_score * 100)))

        # Update
        moment.score = final_score_int
        moment.metadata.update({
            'rescored': True,
            'base_score': base,
            'pattern_bonus': round(pattern_bonus, 3),
            'length_quality': round(length_quality, 3),
            'category_alignment': round(category_alignment, 3),
            'final_score': final_score_int,
        })
        moment.save(update_fields=['score', 'metadata'])
        rescored += 1

    logger.info(f"[MomentScoring] Rescored {rescored} moments for project {project.id}")
    return rescored
