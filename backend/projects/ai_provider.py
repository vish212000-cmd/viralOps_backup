"""
AI Provider Abstraction Layer
==============================
Defines the AIProvider interface and two concrete implementations:

  GeminiProvider   — production, calls Google Gemini 2.5 Flash
  MockAIProvider   — deterministic, used in tests (no network calls)

Usage:
    from projects.ai_provider import get_ai_provider
    provider = get_ai_provider()
    result = provider.generate_social_assets(title, source_type, content_text, ...)
    result = provider.run_content_intelligence(project_id, transcript_text)
    result = provider.detect_moments(transcript_text)

The active provider is selected by the DJANGO_TEST environment variable:
  - If DJANGO_TEST=1  → MockAIProvider
  - Otherwise         → GeminiProvider

In tests, set DJANGO_TEST=1 in settings (done via test settings or DJANGO_SETTINGS_MODULE).
Alternatively, patch 'projects.ai_provider.get_ai_provider' in any test.
"""

from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Base interface
# ---------------------------------------------------------------------------

class AIProvider(ABC):
    """Abstract base for all AI providers."""

    @abstractmethod
    def generate_social_assets(
        self,
        title: str,
        source_type: str,
        content_text: str,
        memory_settings: Optional[dict] = None,
        templates=None,
        transcript_diagnostics: Optional[dict] = None,
    ) -> dict:
        """
        Generate social-ready assets from long-form content.

        Returns dict with keys:
            hooks, titles, captions, ctas, hashtags, thumbnail_copy, scripts
        """

    @abstractmethod
    def run_content_intelligence(
        self,
        project_id: int,
        transcript_text: str,
    ) -> dict:
        """
        Extract structured intelligence from transcript text.

        Returns dict with keys:
            summary, topics, keywords, entities, emotional_moments, viral_score
        """

    @abstractmethod
    def detect_moments(
        self,
        transcript_text: str,
    ) -> list:
        """
        Detect high-value moments in transcript text.

        Returns list of dicts with keys:
            title, category, score, start_time, end_time, excerpt
        """


# ---------------------------------------------------------------------------
# Gemini Provider (production)
# ---------------------------------------------------------------------------

class GeminiProvider(AIProvider):
    """
    Production AI provider backed by Google Gemini 2.5 Flash.
    Requires GEMINI_API_KEY in Django settings.
    """

    def __init__(self):
        from django.conf import settings
        import google.generativeai as genai

        api_key = getattr(settings, 'GEMINI_API_KEY', '') or os.getenv('GEMINI_API_KEY', '')
        if not api_key:
            raise RuntimeError(
                "GeminiProvider requires GEMINI_API_KEY. "
                "Set it in environment variables or Django settings."
            )
        genai.configure(api_key=api_key)
        self._genai = genai
        logger.info("[GeminiProvider] Initialized with Gemini 2.5 Flash")

    def _call_gemini(self, prompt: str) -> str:
        """Make a Gemini API call and return raw text response."""
        model = self._genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Strip markdown code fences
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

    def generate_social_assets(
        self,
        title: str,
        source_type: str,
        content_text: str,
        memory_settings: Optional[dict] = None,
        templates=None,
        transcript_diagnostics: Optional[dict] = None,
    ) -> dict:
        from projects.services.transcript_validator import TranscriptValidationError

        # YouTube gate — must have PASS diagnostics
        if source_type == 'YOUTUBE':
            if transcript_diagnostics is None:
                raise TranscriptValidationError(
                    "Gemini generation blocked: transcript_diagnostics not provided for YOUTUBE source.",
                    diagnostics={"status": "FAIL", "failures": ["transcript_diagnostics missing"]}
                )
            if transcript_diagnostics.get("status") != "PASS":
                failures = transcript_diagnostics.get("failures", ["Unknown validation failure"])
                raise TranscriptValidationError(
                    f"Gemini generation blocked: transcript validation status is "
                    f"'{transcript_diagnostics.get('status')}'. Failures: {'; '.join(failures)}",
                    diagnostics=transcript_diagnostics
                )
            logger.info(
                f"[GeminiProvider] YouTube gate PASS — "
                f"length={transcript_diagnostics.get('length')}, "
                f"method={transcript_diagnostics.get('retrieval_method')}"
            )

        # Build memory/brand voice snippet
        memory_prompt = ""
        if memory_settings:
            def _get(key, fallback):
                val = memory_settings.get(key)
                if isinstance(val, dict):
                    return val.get(list(val.keys())[0], fallback)
                return val or fallback

            memory_prompt = f"""
Tone of Voice: {_get('BRAND_TONE', 'Professional, engaging, and authoritative')}
Style Guide: {_get('STYLE_GUIDE', 'Clear, clean formatting, limit emoji use')}
Preferred Hooks Style: {_get('PREFERRED_HOOKS', '')}
"""

        prompt = f"""
You are an expert social media copywriter and growth marketer.
Analyze the following long-form content text and generate structured short-form social-ready assets.
Base your output STRICTLY on the provided content. Do not invent topics not present in the text.

Content Title: {title}
Source Type: {source_type}

{memory_prompt}

Content text to analyze:
{content_text[:8000]}

You MUST return a JSON object with the exact keys:
1. "hooks": list of 3 high-engaging hook variations for video openers.
2. "titles": list of 3 clickable video title variations.
3. "captions": list of 3 caption options (shorts, reels, tiktok formats).
4. "ctas": list of 3 call-to-action options.
5. "hashtags": list of 8 trending and relevant hashtags.
6. "thumbnail_copy": list of 3 short texts for video thumbnails (max 4 words each).
7. "scripts": list of 2 short video scripts (under 60 seconds each).

Return only valid JSON. Do not include markdown code blocks.
"""
        text = self._call_gemini(prompt)
        result = json.loads(text)
        logger.info(f"[GeminiProvider] Generated social assets for '{title[:50]}'")
        return result

    def run_content_intelligence(self, project_id: int, transcript_text: str) -> dict:
        if not transcript_text or len(transcript_text) < 100:
            logger.warning(f"[GeminiProvider] Transcript too short for project {project_id}")
            return {}

        prompt = f"""
You are a content intelligence expert. Analyze the following transcript and extract structured data.

Transcript (first 6000 chars):
{transcript_text[:6000]}

Return a single valid JSON object with these exact keys:
{{
  "summary": "2-3 sentence summary of the main content",
  "topics": ["topic1", "topic2", "topic3"],
  "keywords": ["kw1", "kw2", "kw3", "kw4", "kw5", "kw6"],
  "entities": [{{"name": "Entity Name", "type": "PERSON|BRAND|PLACE|CONCEPT"}}],
  "emotional_moments": [{{"text": "excerpt", "emotion": "excitement|curiosity|inspiration", "intensity": 7}}],
  "viral_score": 75
}}

Return only valid JSON.
"""
        text = self._call_gemini(prompt)
        data = json.loads(text)
        data['viral_score'] = max(0, min(100, int(data.get('viral_score', 50))))
        logger.info(f"[GeminiProvider] Content intelligence complete for project {project_id}")
        return data

    def detect_moments(self, transcript_text: str) -> list:
        if not transcript_text or len(transcript_text) < 200:
            return []

        prompt = f"""
You are an expert viral content strategist and moment detection AI.
Analyze the following transcript and detect the most impactful moments.

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
    "excerpt": "Direct quote or paraphrase from the transcript (50-120 words)"
  }}
]

Return only valid JSON array.
"""
        text = self._call_gemini(prompt)
        moments = json.loads(text)
        if not isinstance(moments, list):
            return []
        logger.info(f"[GeminiProvider] Detected {len(moments)} moments")
        return moments


# ---------------------------------------------------------------------------
# Mock Provider (tests)
# ---------------------------------------------------------------------------

class MockAIProvider(AIProvider):
    """
    Deterministic AI provider for tests.
    Never makes network calls. Returns fixed, predictable assets.
    """

    # Deterministic mock data — always the same regardless of input
    MOCK_ASSETS = {
        "hooks": [
            "Hook 1: Did you know this changes everything about content?",
            "Hook 2: Most creators get this completely wrong.",
            "Hook 3: Here's the one strategy nobody talks about.",
        ],
        "titles": [
            "Title 1: The Ultimate Guide to Viral Content Creation",
            "Title 2: Why 99% of Creators Fail (And How to Win)",
            "Title 3: How to 10x Your Content Output in 30 Days",
        ],
        "captions": [
            "Caption 1: Transform your content strategy with this proven framework. #ContentCreation",
            "Caption 2: Stop wasting time on content that doesn't convert. Watch this.",
            "Caption 3: The content playbook every creator needs but nobody shares.",
        ],
        "ctas": [
            "CTA 1: Subscribe for weekly content strategy breakdowns.",
            "CTA 2: Comment your biggest content challenge below.",
            "CTA 3: Download the free content calendar in the description.",
        ],
        "hashtags": [
            "#ContentCreation",
            "#ViralContent",
            "#ContentStrategy",
            "#CreatorTips",
            "#DigitalMarketing",
            "#ContentMarketing",
            "#GrowthHacking",
            "#SocialMediaTips",
        ],
        "thumbnail_copy": [
            "NEVER DO THIS",
            "GAME CHANGER",
            "VIRAL FORMULA",
        ],
        "scripts": [
            {
                "platform": "YOUTUBE",
                "script": (
                    "Hook: Most content creators make this one mistake. "
                    "Body: The truth is, virality isn't about luck. "
                    "It's about understanding your audience at a deeper level. "
                    "Here's the three-step framework that changed everything. "
                    "CTA: Subscribe to never miss a strategy breakdown."
                ),
            },
            {
                "platform": "TIKTOK",
                "script": (
                    "POV: You just discovered the content strategy that top creators hide. "
                    "Here's what they're actually doing. "
                    "Step one: nail your hook in the first 2 seconds. "
                    "Follow for more."
                ),
            },
        ],
    }

    MOCK_INTELLIGENCE = {
        "summary": (
            "This content covers key strategies for viral content creation. "
            "The speaker shares actionable frameworks for growing an audience. "
            "Key topics include engagement, retention, and distribution."
        ),
        "topics": ["Content Strategy", "Viral Growth", "Audience Retention", "Distribution"],
        "keywords": ["content", "viral", "strategy", "creator", "growth", "engagement"],
        "entities": [
            {"name": "Content Creator", "type": "CONCEPT"},
            {"name": "YouTube", "type": "BRAND"},
        ],
        "emotional_moments": [
            {"text": "This is the moment that changed everything", "emotion": "inspiration", "intensity": 8},
            {"text": "Most people get this completely wrong", "emotion": "curiosity", "intensity": 7},
        ],
        "viral_score": 78,
    }

    MOCK_MOMENTS = [
        {
            "title": "The Hook That Stops Scrolling",
            "category": "HOOK",
            "score": 92,
            "start_time": "0:05",
            "end_time": "0:30",
            "excerpt": "Most content creators make this one critical mistake that kills their growth.",
        },
        {
            "title": "The Viral Framework Revealed",
            "category": "VIRAL",
            "score": 88,
            "start_time": "1:00",
            "end_time": "1:45",
            "excerpt": "Here's the three-step framework that top creators use but never talk about publicly.",
        },
        {
            "title": "The Personal Story Behind the Strategy",
            "category": "STORY",
            "score": 81,
            "start_time": "2:10",
            "end_time": "3:00",
            "excerpt": "I remember when I first started out, I was making every mistake in the book.",
        },
        {
            "title": "The Emotional Truth About Creator Burnout",
            "category": "EMOTIONAL",
            "score": 79,
            "start_time": "4:20",
            "end_time": "5:10",
            "excerpt": "The real reason most creators quit isn't lack of talent — it's lack of a system.",
        },
        {
            "title": "The Algorithm Insight You Need",
            "category": "EDUCATIONAL",
            "score": 85,
            "start_time": "6:00",
            "end_time": "7:00",
            "excerpt": "Data shows that retention after 30 seconds is the single biggest predictor of viral reach.",
        },
    ]

    def generate_social_assets(
        self,
        title: str,
        source_type: str,
        content_text: str,
        memory_settings: Optional[dict] = None,
        templates=None,
        transcript_diagnostics: Optional[dict] = None,
    ) -> dict:
        # Still enforce the YouTube gate — even mock must respect it
        if source_type == 'YOUTUBE':
            from projects.services.transcript_validator import TranscriptValidationError
            if transcript_diagnostics is None:
                raise TranscriptValidationError(
                    "MockAIProvider: transcript_diagnostics required for YOUTUBE.",
                    diagnostics={"status": "FAIL", "failures": ["transcript_diagnostics missing"]}
                )
            if transcript_diagnostics.get("status") != "PASS":
                raise TranscriptValidationError(
                    f"MockAIProvider: transcript validation failed.",
                    diagnostics=transcript_diagnostics
                )

        logger.debug(f"[MockAIProvider] generate_social_assets called for '{title[:40]}'")
        return dict(self.MOCK_ASSETS)

    def run_content_intelligence(self, project_id: int, transcript_text: str) -> dict:
        logger.debug(f"[MockAIProvider] run_content_intelligence called for project {project_id}")
        return dict(self.MOCK_INTELLIGENCE)

    def detect_moments(self, transcript_text: str) -> list:
        logger.debug("[MockAIProvider] detect_moments called")
        return [dict(m) for m in self.MOCK_MOMENTS]


# ---------------------------------------------------------------------------
# Provider factory
# ---------------------------------------------------------------------------

_provider_instance: Optional[AIProvider] = None


def get_ai_provider() -> AIProvider:
    """
    Return the active AI provider singleton.

    Selection priority:
      1. DJANGO_TEST=1 env var (or settings.TESTING=True)  → MockAIProvider
      2. Otherwise                                          → GeminiProvider
    """
    global _provider_instance
    if _provider_instance is not None:
        return _provider_instance

    # Detect test environment
    is_test = (
        os.getenv('DJANGO_TEST', '') == '1'
        or os.getenv('TESTING', '') == '1'
        or _is_running_tests()
    )

    if is_test:
        logger.info("[AIProvider] Test environment detected — using MockAIProvider")
        _provider_instance = MockAIProvider()
    else:
        logger.info("[AIProvider] Production environment — using GeminiProvider")
        _provider_instance = GeminiProvider()

    return _provider_instance


def _is_running_tests() -> bool:
    """Detect if we're inside Django's test runner."""
    import sys
    argv = sys.argv
    return (
        len(argv) >= 1
        and any(
            'manage.py' in str(a) or 'pytest' in str(a) or 'unittest' in str(a)
            for a in argv
        )
        and any(a in ('test', 'pytest') for a in argv)
    )


def reset_provider() -> None:
    """Reset singleton — used in tests that need a fresh provider."""
    global _provider_instance
    _provider_instance = None


def set_provider(provider: AIProvider) -> None:
    """Inject a specific provider — used in tests."""
    global _provider_instance
    _provider_instance = provider
