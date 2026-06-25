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
    def generate_social_assets_batch(
        self,
        title: str,
        source_type: str,
        moments: list[dict],
        memory_settings: Optional[dict] = None,
        templates=None,
        transcript_diagnostics: Optional[dict] = None,
    ) -> dict:
        """
        Generate social-ready assets for MULTIPLE moments in a single API call.
        moments is a list of dicts: [{"id": 1, "title": "Moment title", "content_text": "excerpt..."}]
        Returns dict mapping moment IDs to their generated asset pack.
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

    def generate_social_assets_batch(
        self,
        title: str,
        source_type: str,
        moments: list[dict],
        memory_settings: Optional[dict] = None,
        templates=None,
        transcript_diagnostics: Optional[dict] = None,
    ) -> dict:
        from projects.services.transcript_validator import TranscriptValidationError

        if source_type == 'YOUTUBE':
            if transcript_diagnostics is None:
                raise TranscriptValidationError(
                    "Gemini batch generation blocked: transcript_diagnostics missing.",
                    diagnostics={"status": "FAIL", "failures": ["transcript_diagnostics missing"]}
                )
            if transcript_diagnostics.get("status") != "PASS":
                failures = transcript_diagnostics.get("failures", ["Unknown validation failure"])
                raise TranscriptValidationError(
                    f"Gemini batch generation blocked: validation status is '{transcript_diagnostics.get('status')}'.",
                    diagnostics=transcript_diagnostics
                )

        memory_prompt = ""
        if memory_settings:
            def _get(key, fallback):
                val = memory_settings.get(key)
                if isinstance(val, dict):
                    return val.get(list(val.keys())[0], fallback)
                return val or fallback
            memory_prompt = f"Tone of Voice: {_get('BRAND_TONE', 'Professional')}\nStyle Guide: {_get('STYLE_GUIDE', 'Clear')}"

        # Build moments context string
        moments_context = ""
        for m in moments:
            m_id = m.get("id")
            m_title = m.get("title", "Unknown")
            m_text = str(m.get("content_text", ""))[:2000]
            moments_context += f"--- MOMENT ID: {m_id} ---\nMoment Title: {m_title}\nMoment Text: {m_text}\n\n"

        prompt = f"""
You are an expert social media copywriter and growth marketer.
Analyze the following MULTIPLE moments and generate a structured asset pack FOR EACH MOMENT in ONE SINGLE RESPONSE.
Base your output STRICTLY on the provided content.

Project Title: {title}
Source Type: {source_type}
{memory_prompt}

{moments_context}

You MUST return a JSON OBJECT where the keys are the EXACT MOMENT IDs provided above (as strings).
For each Moment ID, provide an object with the exact keys:
"hooks": list of 3 high-engaging hook variations for video openers.
"titles": list of 3 clickable video title variations.
"captions": list of 3 caption options (shorts, reels, tiktok formats).
"ctas": list of 3 call-to-action options.
"hashtags": list of 8 trending and relevant hashtags.
"thumbnail_copy": list of 3 short texts for video thumbnails (max 4 words each).
"scripts": list of 2 short video scripts (under 60 seconds each).

Return only valid JSON matching this structure:
{{
  "moment_id_1": {{ "hooks": [...], "titles": [...], ... }},
  "moment_id_2": {{ "hooks": [...], "titles": [...], ... }}
}}
Do not include markdown code blocks.
"""
        text = self._call_gemini(prompt)
        try:
            result = json.loads(text)
            normalized = {}
            for k, v in result.items():
                numeric_k = "".join(filter(str.isdigit, k))
                if numeric_k:
                    normalized[numeric_k] = v
                else:
                    normalized[k] = v
            result = normalized
        except Exception as e:
            logger.error(f"[GeminiProvider] Batch generation JSON parsing failed: {e}")
            raise

        logger.info(f"[GeminiProvider] Batch generated social assets for {len(moments)} moments")
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

    def generate_social_assets_batch(
        self,
        title: str,
        source_type: str,
        moments: list[dict],
        memory_settings: Optional[dict] = None,
        templates=None,
        transcript_diagnostics: Optional[dict] = None,
    ) -> dict:
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
        
        logger.debug(f"[MockAIProvider] generate_social_assets_batch called for {len(moments)} moments")
        result = {}
        for m in moments:
            result[str(m["id"])] = dict(self.MOCK_ASSETS)
        return result

    def run_content_intelligence(self, project_id: int, transcript_text: str) -> dict:
        logger.debug(f"[MockAIProvider] run_content_intelligence called for project {project_id}")
        return dict(self.MOCK_INTELLIGENCE)

    def detect_moments(self, transcript_text: str) -> list:
        logger.debug("[MockAIProvider] detect_moments called")
        return [dict(m) for m in self.MOCK_MOMENTS]


# ---------------------------------------------------------------------------
# NVIDIA Nemotron Provider
# ---------------------------------------------------------------------------

class NvidiaProvider(AIProvider):
    """
    Production AI provider backed by NVIDIA Nemotron via integrate.api.nvidia.com.
    Requires NVIDIA_API_KEY in environment variables.
    """

    def __init__(self):
        self.api_key = os.getenv('NVIDIA_API_KEY', '')
        self.model_name = os.getenv('NVIDIA_MODEL', 'meta/llama-3.1-70b-instruct')
        if not self.api_key:
            raise RuntimeError(
                "NvidiaProvider requires NVIDIA_API_KEY. "
                "Set it in environment variables."
            )
        logger.info(f"[NvidiaProvider] Initialized with model {self.model_name}")

    def _call_nvidia(self, prompt: str) -> str:
        """Make a NVIDIA API call and return raw text response."""
        import requests
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2000
        }
        import time
        start_time = time.time()
        
        try:
            response = requests.post(
                "https://integrate.api.nvidia.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=300
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.Timeout:
            logger.error("NVIDIA API timed out after 300s")
            raise RuntimeError("NVIDIA API timed out")
        except requests.exceptions.RequestException as e:
            logger.error(f"NVIDIA API request failed: {e}")
            raise RuntimeError(f"NVIDIA API request failed: {str(e)}")
        except ValueError as e:
            logger.error(f"NVIDIA API returned invalid JSON: {e}")
            raise RuntimeError(f"NVIDIA API returned invalid JSON: {str(e)}")
            
        logger.info(f"NVIDIA TIME: {time.time() - start_time}")
        
        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("NVIDIA API returned empty response choices")
            
        text = choices[0].get("message", {}).get("content", "").strip()
        if not text:
            raise RuntimeError("NVIDIA API returned empty message content")
        
        # Robustly extract JSON block if conversational text surrounds it
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.rfind("```")
            if end > start:
                text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.rfind("```")
            if end > start:
                text = text[start:end].strip()
        else:
            # Fallback to finding the first { or [ and the last } or ]
            first_brace = text.find("{")
            first_bracket = text.find("[")
            last_brace = text.rfind("}")
            last_bracket = text.rfind("]")
            
            first_idx = -1
            if first_brace != -1 and first_bracket != -1:
                first_idx = min(first_brace, first_bracket)
            elif first_brace != -1:
                first_idx = first_brace
            elif first_bracket != -1:
                first_idx = first_bracket
                
            last_idx = -1
            if last_brace != -1 and last_bracket != -1:
                last_idx = max(last_brace, last_bracket)
            elif last_brace != -1:
                last_idx = last_brace
            elif last_bracket != -1:
                last_idx = last_bracket
                
            if first_idx != -1 and last_idx != -1 and last_idx >= first_idx:
                text = text[first_idx:last_idx + 1].strip()

        return text

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

        if source_type == 'YOUTUBE':
            if transcript_diagnostics is None:
                raise TranscriptValidationError(
                    "Nvidia generation blocked: transcript_diagnostics missing.",
                    diagnostics={"status": "FAIL", "failures": ["transcript_diagnostics missing"]}
                )
            if transcript_diagnostics.get("status") != "PASS":
                failures = transcript_diagnostics.get("failures", ["Unknown validation failure"])
                raise TranscriptValidationError(
                    f"Nvidia generation blocked: validation status is '{transcript_diagnostics.get('status')}'.",
                    diagnostics=transcript_diagnostics
                )

        memory_prompt = ""
        if memory_settings:
            def _get(key, fallback):
                val = memory_settings.get(key)
                if isinstance(val, dict):
                    return val.get(list(val.keys())[0], fallback)
                return val or fallback

            memory_prompt = f"Tone of Voice: {_get('BRAND_TONE', 'Professional')}\nStyle Guide: {_get('STYLE_GUIDE', 'Clear')}"

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
        text = self._call_nvidia(prompt)
        try:
            result = json.loads(text)
            assert isinstance(result, dict), "NVIDIA AI response must be a JSON dictionary"
            assert len(result.keys()) > 0, "NVIDIA AI response dictionary cannot be empty"
        except (json.decoder.JSONDecodeError, AssertionError) as e:
            logger.error(f"[NvidiaProvider] generate_social_assets JSON parsing failed: {e}")
            raise RuntimeError(f"NVIDIA AI returned invalid JSON format: {str(e)}")
            
        logger.info(f"[NvidiaProvider] Generated social assets for '{title[:50]}'")
        return result

    def generate_social_assets_batch(
        self,
        title: str,
        source_type: str,
        moments: list[dict],
        memory_settings: Optional[dict] = None,
        templates=None,
        transcript_diagnostics: Optional[dict] = None,
    ) -> dict:
        from projects.services.transcript_validator import TranscriptValidationError

        if source_type == 'YOUTUBE':
            if transcript_diagnostics is None:
                raise TranscriptValidationError(
                    "Nvidia batch generation blocked: transcript_diagnostics missing.",
                    diagnostics={"status": "FAIL", "failures": ["transcript_diagnostics missing"]}
                )
            if transcript_diagnostics.get("status") != "PASS":
                failures = transcript_diagnostics.get("failures", ["Unknown validation failure"])
                raise TranscriptValidationError(
                    f"Nvidia batch generation blocked: validation status is '{transcript_diagnostics.get('status')}'.",
                    diagnostics=transcript_diagnostics
                )

        memory_prompt = ""
        if memory_settings:
            def _get(key, fallback):
                val = memory_settings.get(key)
                if isinstance(val, dict):
                    return val.get(list(val.keys())[0], fallback)
                return val or fallback
            memory_prompt = f"Tone of Voice: {_get('BRAND_TONE', 'Professional')}\nStyle Guide: {_get('STYLE_GUIDE', 'Clear')}"

        moments_context = ""
        for m in moments:
            m_id = m.get("id")
            m_title = m.get("title", "Unknown")
            m_text = str(m.get("content_text", ""))[:2000]
            moments_context += f"--- MOMENT ID: {m_id} ---\nMoment Title: {m_title}\nMoment Text: {m_text}\n\n"

        prompt = f"""
You are an expert social media copywriter and growth marketer.
Analyze the following MULTIPLE moments and generate a structured asset pack FOR EACH MOMENT in ONE SINGLE RESPONSE.
Base your output STRICTLY on the provided content.

Project Title: {title}
Source Type: {source_type}
{memory_prompt}

{moments_context}

You MUST return a JSON OBJECT where the keys are the EXACT MOMENT IDs provided above (as strings).
For each Moment ID, provide an object with the exact keys:
"hooks": list of 3 high-engaging hook variations for video openers.
"titles": list of 3 clickable video title variations.
"captions": list of 3 caption options (shorts, reels, tiktok formats).
"ctas": list of 3 call-to-action options.
"hashtags": list of 8 trending and relevant hashtags.
"thumbnail_copy": list of 3 short texts for video thumbnails (max 4 words each).
"scripts": list of 2 short video scripts (under 60 seconds each).

Return only valid JSON matching this structure:
{{
  "moment_id_1": {{ "hooks": [...], "titles": [...], ... }},
  "moment_id_2": {{ "hooks": [...], "titles": [...], ... }}
}}
Do not include markdown code blocks.
"""
        text = self._call_nvidia(prompt)
        try:
            result = json.loads(text)
            assert isinstance(result, dict), "NVIDIA AI response must be a JSON dictionary"
            assert len(result.keys()) > 0, "NVIDIA AI response dictionary cannot be empty"
            normalized = {}
            for k, v in result.items():
                numeric_k = "".join(filter(str.isdigit, k))
                if numeric_k:
                    normalized[numeric_k] = v
                else:
                    normalized[k] = v
            result = normalized
        except Exception as e:
            logger.error(f"[NvidiaProvider] Batch generation JSON parsing failed: {e}")
            raise

        logger.info(f"[NvidiaProvider] Batch generated social assets for {len(moments)} moments")
        return result

    def run_content_intelligence(self, project_id: int, transcript_text: str) -> dict:
        if not transcript_text or len(transcript_text) < 100:
            logger.warning(f"[NvidiaProvider] Transcript too short for project {project_id}")
            return {}

        prompt = f"""
You are a content intelligence expert. Analyze the following transcript and extract structured data.

Transcript (first 2000 chars):
{transcript_text[:2000]}

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
        text = self._call_nvidia(prompt)
        try:
            data = json.loads(text)
        except json.decoder.JSONDecodeError as e:
            logger.error(f"[NvidiaProvider] run_content_intelligence JSON parsing failed: {e}")
            return {}
            
        data['viral_score'] = max(0, min(100, int(data.get('viral_score', 50))))
        logger.info(f"[NvidiaProvider] Content intelligence complete for project {project_id}")
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
        text = self._call_nvidia(prompt)
        try:
            moments = json.loads(text)
        except json.decoder.JSONDecodeError as e:
            logger.error(f"[NvidiaProvider] detect_moments JSON parsing failed: {e}")
            return []
            
        if not isinstance(moments, list):
            return []
        logger.info(f"[NvidiaProvider] Detected {len(moments)} moments")
        return moments



# ---------------------------------------------------------------------------
# OpenRouter Provider
# ---------------------------------------------------------------------------

class OpenRouterProvider(AIProvider):
    """
    AI provider backed by OpenRouter.
    Implements model chaining/fallback for free tier models.
    """

    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY', '')
        if not self.api_key:
            raise RuntimeError("OpenRouterProvider requires OPENROUTER_API_KEY.")
            
        self.models = [
            "meta-llama/llama-3.3-70b-instruct:free",
            "nousresearch/hermes-3-llama-3.1-405b:free"
        ]
        logger.info(f"[OpenRouterProvider] Initialized with models: {self.models}")

    def _call_openrouter(self, prompt: str) -> str:
        import time
        import requests
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://viralops.app",
            "X-Title": "ViralOps"
        }
        
        last_exception = None
        for model in self.models:
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
            start_time = time.time()
            try:
                logger.info(f"[OpenRouterProvider] Calling {model}")
                response = requests.post(url, headers=headers, json=payload, timeout=45)
                response.raise_for_status()
                data = response.json()
                text = data['choices'][0]['message']['content'].strip()
                
                # Strip markdown code fences
                if text.startswith("```json"):
                    text = text[7:]
                if text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                    
                duration = time.time() - start_time
                usage = data.get('usage', {})
                logger.info(f"[OpenRouterProvider] {model} succeeded in {duration:.2f}s, tokens: {usage}")
                return text.strip()
            except Exception as e:
                logger.warning(f"[OpenRouterProvider] {model} failed: {e}")
                last_exception = e
                continue
                
        raise last_exception or RuntimeError("All OpenRouter models failed")

    # Re-use Gemini logic for prompt building, calling self._call_openrouter
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

        if source_type == 'YOUTUBE':
            if transcript_diagnostics is None:
                raise TranscriptValidationError(
                    "OpenRouter generation blocked: transcript_diagnostics missing.",
                    diagnostics={"status": "FAIL", "failures": ["transcript_diagnostics missing"]}
                )
            if transcript_diagnostics.get("status") != "PASS":
                failures = transcript_diagnostics.get("failures", ["Unknown validation failure"])
                raise TranscriptValidationError(
                    f"OpenRouter generation blocked: validation status is '{transcript_diagnostics.get('status')}'.",
                    diagnostics=transcript_diagnostics
                )

        memory_prompt = ""
        if memory_settings:
            def _get(key, fallback):
                val = memory_settings.get(key)
                if isinstance(val, dict):
                    return val.get(list(val.keys())[0], fallback)
                return val or fallback
            memory_prompt = f"Tone of Voice: {_get('BRAND_TONE', 'Professional')}\nStyle Guide: {_get('STYLE_GUIDE', 'Clear')}"

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
        text = self._call_openrouter(prompt)
        try:
            result = json.loads(text)
            assert isinstance(result, dict), "OpenRouter API response must be a JSON dictionary"
            assert len(result.keys()) > 0, "OpenRouter API response dictionary cannot be empty"
        except (json.decoder.JSONDecodeError, AssertionError) as e:
            logger.error(f"[OpenRouterProvider] generate_social_assets JSON parsing failed: {e}")
            raise RuntimeError(f"OpenRouter API returned invalid JSON format: {str(e)}")
            
        logger.info(f"[OpenRouterProvider] Generated social assets for '{title[:50]}'")
        return result

    def generate_social_assets_batch(
        self,
        title: str,
        source_type: str,
        moments: list[dict],
        memory_settings: Optional[dict] = None,
        templates=None,
        transcript_diagnostics: Optional[dict] = None,
    ) -> dict:
        from projects.services.transcript_validator import TranscriptValidationError

        if source_type == 'YOUTUBE':
            if transcript_diagnostics is None:
                raise TranscriptValidationError(
                    "OpenRouter batch generation blocked: transcript_diagnostics missing.",
                    diagnostics={"status": "FAIL", "failures": ["transcript_diagnostics missing"]}
                )
            if transcript_diagnostics.get("status") != "PASS":
                failures = transcript_diagnostics.get("failures", ["Unknown validation failure"])
                raise TranscriptValidationError(
                    f"OpenRouter batch generation blocked: validation status is '{transcript_diagnostics.get('status')}'.",
                    diagnostics=transcript_diagnostics
                )

        memory_prompt = ""
        if memory_settings:
            def _get(key, fallback):
                val = memory_settings.get(key)
                if isinstance(val, dict):
                    return val.get(list(val.keys())[0], fallback)
                return val or fallback
            memory_prompt = f"Tone of Voice: {_get('BRAND_TONE', 'Professional')}\nStyle Guide: {_get('STYLE_GUIDE', 'Clear')}"

        moments_context = ""
        for m in moments:
            m_id = m.get("id")
            m_title = m.get("title", "Unknown")
            m_text = str(m.get("content_text", ""))[:2000]
            moments_context += f"--- MOMENT ID: {m_id} ---\nMoment Title: {m_title}\nMoment Text: {m_text}\n\n"

        prompt = f"""
You are an expert social media copywriter and growth marketer.
Analyze the following MULTIPLE moments and generate a structured asset pack FOR EACH MOMENT in ONE SINGLE RESPONSE.
Base your output STRICTLY on the provided content.

Project Title: {title}
Source Type: {source_type}
{memory_prompt}

{moments_context}

You MUST return a JSON OBJECT where the keys are the EXACT MOMENT IDs provided above (as strings).
For each Moment ID, provide an object with the exact keys:
"hooks": list of 3 high-engaging hook variations for video openers.
"titles": list of 3 clickable video title variations.
"captions": list of 3 caption options (shorts, reels, tiktok formats).
"ctas": list of 3 call-to-action options.
"hashtags": list of 8 trending and relevant hashtags.
"thumbnail_copy": list of 3 short texts for video thumbnails (max 4 words each).
"scripts": list of 2 short video scripts (under 60 seconds each).

Return only valid JSON matching this structure:
{{
  "moment_id_1": {{ "hooks": [...], "titles": [...], ... }},
  "moment_id_2": {{ "hooks": [...], "titles": [...], ... }}
}}
Do not include markdown code blocks.
"""
        text = self._call_openrouter(prompt)
        try:
            result = json.loads(text)
            assert isinstance(result, dict), "OpenRouter API response must be a JSON dictionary"
            assert len(result.keys()) > 0, "OpenRouter API response dictionary cannot be empty"
            normalized = {}
            for k, v in result.items():
                numeric_k = "".join(filter(str.isdigit, k))
                if numeric_k:
                    normalized[numeric_k] = v
                else:
                    normalized[k] = v
            result = normalized
        except Exception as e:
            logger.error(f"[OpenRouterProvider] Batch generation JSON parsing failed: {e}")
            raise

        logger.info(f"[OpenRouterProvider] Batch generated social assets for {len(moments)} moments")
        return result
        
    def run_content_intelligence(self, project_id: int, transcript_text: str) -> dict:
        if not transcript_text or len(transcript_text) < 100:
            logger.warning(f"[OpenRouterProvider] Transcript too short for project {project_id}")
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
        text = self._call_openrouter(prompt)
        data = json.loads(text)
        data['viral_score'] = max(0, min(100, int(data.get('viral_score', 50))))
        logger.info(f"[OpenRouterProvider] Content intelligence complete for project {project_id}")
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
        text = self._call_openrouter(prompt)
        moments = json.loads(text)
        if not isinstance(moments, list):
            return []
        logger.info(f"[OpenRouterProvider] Detected {len(moments)} moments")
        return moments



# ---------------------------------------------------------------------------
# Provider Router
# ---------------------------------------------------------------------------

class ProviderRouter(AIProvider):
    """
    Chains multiple AI providers to ensure high availability.
    Order: NvidiaProvider -> OpenRouterProvider -> GeminiProvider
    """

    def __init__(self):
        self.providers = []
        
        # 1. NVIDIA
        if os.getenv('NVIDIA_API_KEY'):
            try:
                self.providers.append(NvidiaProvider())
            except Exception as e:
                logger.warning(f"[ProviderRouter] Failed to init NvidiaProvider: {e}")
                
        # 2. OpenRouter
        if os.getenv('OPENROUTER_API_KEY'):
            try:
                self.providers.append(OpenRouterProvider())
            except Exception as e:
                logger.warning(f"[ProviderRouter] Failed to init OpenRouterProvider: {e}")
                
        # 3. Gemini
        if os.getenv('GEMINI_API_KEY'):
            try:
                self.providers.append(GeminiProvider())
            except Exception as e:
                logger.warning(f"[ProviderRouter] Failed to init GeminiProvider: {e}")
                
        if not self.providers:
            logger.warning("[ProviderRouter] No providers configured! Falling back to MockAIProvider.")
            self.providers.append(MockAIProvider())
            
        logger.info(f"[ProviderRouter] Initialized chain: {[p.__class__.__name__ for p in self.providers]}")

    def _route(self, method_name, *args, **kwargs):
        last_exception = None
        for provider in self.providers:
            try:
                logger.info(f"[ProviderRouter] Attempting {method_name} with {provider.__class__.__name__}")
                method = getattr(provider, method_name)
                return method(*args, **kwargs)
            except Exception as e:
                logger.warning(f"[ProviderRouter] {provider.__class__.__name__} failed {method_name}: {e}")
                last_exception = e
                continue
        logger.error(f"[ProviderRouter] All providers failed for {method_name}")
        if last_exception:
            raise last_exception
        raise RuntimeError(f"All AI providers failed for {method_name}")

    def generate_social_assets(self, *args, **kwargs):
        return self._route('generate_social_assets', *args, **kwargs)

    def generate_social_assets_batch(self, *args, **kwargs):
        return self._route('generate_social_assets_batch', *args, **kwargs)

    def run_content_intelligence(self, *args, **kwargs):
        return self._route('run_content_intelligence', *args, **kwargs)

    def detect_moments(self, *args, **kwargs):
        return self._route('detect_moments', *args, **kwargs)


# ---------------------------------------------------------------------------
# Provider factory
# ---------------------------------------------------------------------------

_provider_instance: Optional[AIProvider] = None



def get_ai_provider() -> AIProvider:
    """
    Return the active AI provider singleton.

    Selection priority:
      1. DJANGO_TEST=1 env var (or settings.TESTING=True)  → MockAIProvider
      2. Otherwise                                          → ProviderRouter
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
        logger.info("[AIProvider] Production environment — using ProviderRouter")
        _provider_instance = ProviderRouter()

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
