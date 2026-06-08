"""
AI Service — thin routing layer.

All Gemini logic now lives in GeminiProvider (projects/ai_provider.py).
This module exists to preserve the public API used by tasks.py and views.py.

Production: delegates to GeminiProvider
Tests:      delegates to MockAIProvider (no network calls)
"""

import logging
from projects.ai_provider import get_ai_provider

logger = logging.getLogger(__name__)


def generate_social_assets(
    title: str,
    source_type: str,
    content_text: str,
    memory_settings: dict = None,
    templates=None,
    transcript_diagnostics: dict = None,
) -> dict:
    """
    Generate social-ready assets from long-form content.

    Delegates to the active AI provider (Gemini in production, Mock in tests).
    YouTube transcript gate is enforced inside the provider.

    Returns:
        dict with hooks, titles, captions, ctas, hashtags, thumbnail_copy, scripts
    """
    provider = get_ai_provider()
    return provider.generate_social_assets(
        title=title,
        source_type=source_type,
        content_text=content_text,
        memory_settings=memory_settings,
        templates=templates,
        transcript_diagnostics=transcript_diagnostics,
    )
