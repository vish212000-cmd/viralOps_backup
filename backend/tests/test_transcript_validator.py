"""
Test suite for TranscriptValidator (Phase 8).

Tests cover all validation rules as specified:
  - test_valid_transcript_passes
  - test_empty_transcript_fails
  - test_short_transcript_fails
  - test_mock_transcript_fails
  - test_placeholder_transcript_fails
  - test_fallback_transcript_fails
  - test_simulated_transcript_fails
  - test_missing_source_fails
  - test_missing_method_fails
  - test_gemini_blocked_on_validation_failure
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from projects.services.transcript_validator import (
    TranscriptValidationError,
    validate_transcript,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_TRANSCRIPT = (
    "In this video we're going to talk about how content creators can build sustainable "
    "audiences by focusing on authentic storytelling rather than chasing viral trends. "
    "The key insight is that consistency beats virality every single time. "
    "Let me walk you through the three pillars of sustainable content growth: "
    "first, establishing a clear niche identity that resonates with a specific community; "
    "second, developing a repeatable production workflow that doesn't burn you out; "
    "and third, building genuine relationships with your audience through regular engagement. "
    "Now I want to dig into each of these pillars with real-world examples from creators "
    "who have built audiences of over a million subscribers without a single viral video. "
    "The first creator I want to mention focuses entirely on woodworking tutorials... "
) * 3  # ~1200 chars × 3 = well over 1000

VALID_METHOD = "youtube-transcript-api/manual-en"
VALID_TIMESTAMP = datetime(2024, 6, 1, 12, 0, 0)
VALID_SOURCE = "youtube"


# ---------------------------------------------------------------------------
# Test 1 — valid transcript passes
# ---------------------------------------------------------------------------

def test_valid_transcript_passes():
    result = validate_transcript(
        transcript_text=VALID_TRANSCRIPT,
        source_type=VALID_SOURCE,
        retrieval_method=VALID_METHOD,
        retrieval_timestamp=VALID_TIMESTAMP,
    )
    assert result["status"] == "PASS"
    assert result["length"] == len(VALID_TRANSCRIPT)
    assert result["source"] == "youtube"
    assert result["retrieval_method"] == VALID_METHOD
    assert result["retrieval_timestamp"] == VALID_TIMESTAMP.isoformat()
    assert len(result["transcript_preview"]) <= 503  # 500 + "..."


# ---------------------------------------------------------------------------
# Test 2 — empty transcript fails
# ---------------------------------------------------------------------------

def test_empty_transcript_fails():
    with pytest.raises(TranscriptValidationError) as exc_info:
        validate_transcript(
            transcript_text="",
            source_type=VALID_SOURCE,
            retrieval_method=VALID_METHOD,
            retrieval_timestamp=VALID_TIMESTAMP,
        )
    assert exc_info.value.diagnostics["status"] == "FAIL"
    failures = exc_info.value.diagnostics["failures"]
    assert any("empty" in f or "null" in f for f in failures)


# ---------------------------------------------------------------------------
# Test 3 — short transcript fails (< 1000 chars)
# ---------------------------------------------------------------------------

def test_short_transcript_fails():
    short_text = "Short text"
    assert len(short_text) <= 10

    with pytest.raises(TranscriptValidationError) as exc_info:
        validate_transcript(
            transcript_text=short_text,
            source_type=VALID_SOURCE,
            retrieval_method=VALID_METHOD,
            retrieval_timestamp=VALID_TIMESTAMP,
        )
    assert exc_info.value.diagnostics["status"] == "FAIL"
    failures = exc_info.value.diagnostics["failures"]
    assert any("short" in f or "1000" in f for f in failures)


# ---------------------------------------------------------------------------
# Test 4 — mock transcript fails
# ---------------------------------------------------------------------------

def test_mock_transcript_fails():
    mock_text = (
        "mock transcript content for testing purposes. " * 50
    )
    assert len(mock_text) > 1000

    with pytest.raises(TranscriptValidationError) as exc_info:
        validate_transcript(
            transcript_text=mock_text,
            source_type=VALID_SOURCE,
            retrieval_method=VALID_METHOD,
            retrieval_timestamp=VALID_TIMESTAMP,
        )
    assert exc_info.value.diagnostics["status"] == "FAIL"
    failures = exc_info.value.diagnostics["failures"]
    assert any("mock transcript" in f for f in failures)


# ---------------------------------------------------------------------------
# Test 5 — placeholder transcript fails
# ---------------------------------------------------------------------------

def test_placeholder_transcript_fails():
    placeholder_text = (
        "This is placeholder content for the transcript extraction module. " * 40
    )
    assert len(placeholder_text) > 1000

    with pytest.raises(TranscriptValidationError) as exc_info:
        validate_transcript(
            transcript_text=placeholder_text,
            source_type=VALID_SOURCE,
            retrieval_method=VALID_METHOD,
            retrieval_timestamp=VALID_TIMESTAMP,
        )
    assert exc_info.value.diagnostics["status"] == "FAIL"
    failures = exc_info.value.diagnostics["failures"]
    assert any("placeholder" in f for f in failures)


# ---------------------------------------------------------------------------
# Test 6 — fallback transcript fails
# ---------------------------------------------------------------------------

def test_fallback_transcript_fails():
    fallback_text = (
        "This is a fallback transcript generated when real extraction failed. " * 30
    )
    assert len(fallback_text) > 1000

    with pytest.raises(TranscriptValidationError) as exc_info:
        validate_transcript(
            transcript_text=fallback_text,
            source_type=VALID_SOURCE,
            retrieval_method=VALID_METHOD,
            retrieval_timestamp=VALID_TIMESTAMP,
        )
    assert exc_info.value.diagnostics["status"] == "FAIL"
    failures = exc_info.value.diagnostics["failures"]
    assert any("fallback" in f for f in failures)


# ---------------------------------------------------------------------------
# Test 7 — simulated transcript fails
# ---------------------------------------------------------------------------

def test_simulated_transcript_fails():
    simulated_text = (
        "This is a simulated transcript for the YouTube video (https://youtube.com/watch?v=abc123). "
        "The video discusses top strategies for scaling social channels and audience retention. " * 20
    )
    assert len(simulated_text) > 1000

    with pytest.raises(TranscriptValidationError) as exc_info:
        validate_transcript(
            transcript_text=simulated_text,
            source_type=VALID_SOURCE,
            retrieval_method=VALID_METHOD,
            retrieval_timestamp=VALID_TIMESTAMP,
        )
    assert exc_info.value.diagnostics["status"] == "FAIL"
    failures = exc_info.value.diagnostics["failures"]
    assert any("simulated" in f for f in failures)


# ---------------------------------------------------------------------------
# Test 8 — missing source fails
# ---------------------------------------------------------------------------

def test_missing_source_fails():
    with pytest.raises(TranscriptValidationError) as exc_info:
        validate_transcript(
            transcript_text=VALID_TRANSCRIPT,
            source_type="",   # empty
            retrieval_method=VALID_METHOD,
            retrieval_timestamp=VALID_TIMESTAMP,
        )
    assert exc_info.value.diagnostics["status"] == "FAIL"
    failures = exc_info.value.diagnostics["failures"]
    assert any("youtube" in f for f in failures)


def test_wrong_source_fails():
    with pytest.raises(TranscriptValidationError) as exc_info:
        validate_transcript(
            transcript_text=VALID_TRANSCRIPT,
            source_type="vimeo",
            retrieval_method=VALID_METHOD,
            retrieval_timestamp=VALID_TIMESTAMP,
        )
    assert exc_info.value.diagnostics["status"] == "FAIL"


# ---------------------------------------------------------------------------
# Test 9 — missing retrieval method fails
# ---------------------------------------------------------------------------

def test_missing_method_fails():
    with pytest.raises(TranscriptValidationError) as exc_info:
        validate_transcript(
            transcript_text=VALID_TRANSCRIPT,
            source_type=VALID_SOURCE,
            retrieval_method="",   # empty
            retrieval_timestamp=VALID_TIMESTAMP,
        )
    assert exc_info.value.diagnostics["status"] == "FAIL"
    failures = exc_info.value.diagnostics["failures"]
    assert any("retrieval_method" in f for f in failures)


def test_none_method_fails():
    with pytest.raises(TranscriptValidationError) as exc_info:
        validate_transcript(
            transcript_text=VALID_TRANSCRIPT,
            source_type=VALID_SOURCE,
            retrieval_method=None,
            retrieval_timestamp=VALID_TIMESTAMP,
        )
    assert exc_info.value.diagnostics["status"] == "FAIL"


# ---------------------------------------------------------------------------
# Test 10 — missing timestamp fails
# ---------------------------------------------------------------------------

def test_missing_timestamp_fails():
    with pytest.raises(TranscriptValidationError) as exc_info:
        validate_transcript(
            transcript_text=VALID_TRANSCRIPT,
            source_type=VALID_SOURCE,
            retrieval_method=VALID_METHOD,
            retrieval_timestamp=None,
        )
    assert exc_info.value.diagnostics["status"] == "FAIL"
    failures = exc_info.value.diagnostics["failures"]
    assert any("timestamp" in f for f in failures)


# ---------------------------------------------------------------------------
# Test 11 — Gemini blocked on validation failure
# ---------------------------------------------------------------------------

def test_gemini_blocked_on_validation_failure():
    """
    Ensure generate_social_assets raises TranscriptValidationError
    when transcript_diagnostics has status != PASS.
    """
    import django
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viralops.settings.local')
    try:
        django.setup()
    except RuntimeError:
        pass  # Already setup

    from projects.ai_service import generate_social_assets

    failed_diagnostics = {
        "status": "FAIL",
        "length": 0,
        "source": "youtube",
        "retrieval_method": None,
        "retrieval_timestamp": None,
        "transcript_preview": "",
        "failures": ["transcript_text is empty or null"],
    }

    with pytest.raises(TranscriptValidationError) as exc_info:
        generate_social_assets(
            title="Test Video",
            source_type="YOUTUBE",
            content_text="",
            transcript_diagnostics=failed_diagnostics,
        )

    assert "MockAIProvider: transcript validation failed." in str(exc_info.value)
    assert exc_info.value.diagnostics["status"] == "FAIL"


def test_gemini_blocked_when_no_diagnostics_for_youtube():
    """Gemini must be blocked if diagnostics are missing entirely for YouTube."""
    import django
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viralops.settings.local')
    try:
        django.setup()
    except RuntimeError:
        pass

    from projects.ai_service import generate_social_assets

    with pytest.raises(TranscriptValidationError) as exc_info:
        generate_social_assets(
            title="Test Video",
            source_type="YOUTUBE",
            content_text=VALID_TRANSCRIPT,
            transcript_diagnostics=None,  # Missing!
        )

    assert "MockAIProvider: transcript_diagnostics required for YOUTUBE." in str(exc_info.value)
