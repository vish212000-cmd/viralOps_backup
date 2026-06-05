"""
AI Service — Gemini social asset generation.

CRITICAL GATE:
  For YouTube sources, validate_transcript() MUST be called before
  generate_social_assets() is invoked. If validation fails, this function
  will raise TranscriptValidationError and Gemini will NOT execute.

  The mock fallback has been removed. If the Gemini API key is not configured,
  this function raises RuntimeError rather than silently returning mock data.
"""

import os
import json
import logging
from django.conf import settings
import google.generativeai as genai

logger = logging.getLogger(__name__)

# Configure Gemini if key is present
if getattr(settings, 'GEMINI_API_KEY', ''):
    genai.configure(api_key=settings.GEMINI_API_KEY)


def generate_social_assets(
    title: str,
    source_type: str,
    content_text: str,
    memory_settings: dict = None,
    templates=None,
    transcript_diagnostics: dict = None,
) -> dict:
    """
    Call Gemini API to generate short-form social assets from long-form content.

    For YouTube sources, transcript_diagnostics must be provided with status='PASS'.
    This function enforces the Gemini execution gate for YouTube — it will raise
    TranscriptValidationError if validation was not passed upstream.

    Args:
        title:                  Content title.
        source_type:            Source type string (e.g. 'YOUTUBE', 'PDF').
        content_text:           The validated transcript or article text.
        memory_settings:        Optional brand voice memory dict.
        templates:              Optional template overrides (unused currently).
        transcript_diagnostics: Required for YOUTUBE sources. Must have status='PASS'.

    Returns:
        Parsed JSON dict with hooks, titles, captions, ctas, hashtags, thumbnail_copy, scripts.

    Raises:
        TranscriptValidationError: If source is YouTube and diagnostics show FAIL.
        RuntimeError:              If Gemini API key is not configured.
        Exception:                 If Gemini API call fails.
    """
    from projects.services.transcript_validator import TranscriptValidationError

    # --- GEMINI EXECUTION GATE (YouTube) ------------------------------------
    if source_type == 'YOUTUBE':
        if transcript_diagnostics is None:
            raise TranscriptValidationError(
                "Gemini generation blocked: transcript_diagnostics not provided for YOUTUBE source. "
                "validate_transcript() must be called before generate_social_assets().",
                diagnostics={"status": "FAIL", "failures": ["transcript_diagnostics missing"]}
            )
        if transcript_diagnostics.get("status") != "PASS":
            failures = transcript_diagnostics.get("failures", ["Unknown validation failure"])
            raise TranscriptValidationError(
                f"Gemini generation blocked: transcript validation status is "
                f"'{transcript_diagnostics.get('status')}'. "
                f"Failures: {'; '.join(failures)}",
                diagnostics=transcript_diagnostics
            )
        logger.info(
            f"[GeminiGate] PASS — YouTube transcript validated. "
            f"Length={transcript_diagnostics.get('length')}, "
            f"Method={transcript_diagnostics.get('retrieval_method')}"
        )

    # --- Build memory/brand voice prompt snippet ---------------------------
    memory_prompt = ""
    if memory_settings:
        brand_tone_val = memory_settings.get('BRAND_TONE')
        brand_tone = (
            brand_tone_val.get('tone', 'Professional, engaging, and authoritative')
            if isinstance(brand_tone_val, dict)
            else (brand_tone_val or 'Professional, engaging, and authoritative')
        )

        style_guide_val = memory_settings.get('STYLE_GUIDE')
        style_guide = (
            style_guide_val.get('guide', 'Clear, clean formatting, limit emoji use')
            if isinstance(style_guide_val, dict)
            else (style_guide_val or 'Clear, clean formatting, limit emoji use')
        )

        preferred_hooks_val = memory_settings.get('PREFERRED_HOOKS')
        preferred_hooks = (
            preferred_hooks_val.get('hooks', '')
            if isinstance(preferred_hooks_val, dict)
            else (preferred_hooks_val or '')
        )

        memory_prompt = f"""
        Tone of Voice: {brand_tone}
        Style Guide: {style_guide}
        Preferred Hooks Style: {preferred_hooks}
        """

    # --- Build Gemini prompt -----------------------------------------------
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
4. "ctas": list of 3 call-to-action options (e.g. follow, comment, download link).
5. "hashtags": list of 8 trending and relevant hashtags.
6. "thumbnail_copy": list of 3 short, punchy texts to display on video thumbnails (max 4 words each).
7. "scripts": list of 2 short video script scripts (under 60 seconds each), with visual prompts and spoken words.

Ensure your output is valid JSON. Do not include markdown code block styling, start directly with {{.
"""

    # --- Gemini API call ----------------------------------------------------
    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    if not api_key:
        raise RuntimeError(
            "Gemini API key not configured. Set GEMINI_API_KEY in environment variables. "
            "No mock fallback is available — real API key required."
        )

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        text_response = response.text.strip()

        # Strip markdown wrappers if present
        if text_response.startswith("```json"):
            text_response = text_response[7:]
        if text_response.startswith("```"):
            text_response = text_response[3:]
        if text_response.endswith("```"):
            text_response = text_response[:-3]
        text_response = text_response.strip()

        parsed_data = json.loads(text_response)
        logger.info(
            f"[GeminiService] Successfully generated assets. "
            f"Source={source_type}, Title='{title[:50]}'"
        )
        return parsed_data

    except Exception as e:
        logger.error(f"[GeminiService] Gemini API generation failed: {e}")
        raise
