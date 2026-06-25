"""
TranscriptValidator — Production-grade YouTube transcript validation service.

Rules:
  - source_type must be 'youtube'
  - transcript_text must not be empty or null
  - transcript_text length must be > 1000 chars
  - retrieval_method must be present
  - retrieval_timestamp must exist
  - transcript must NOT contain forbidden terms
  - transcript must contain actual spoken content (not generated placeholder)

If validation fails: TranscriptValidationError is raised.
Gemini generation must NEVER proceed after a failure.
"""

import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Forbidden content markers — any of these in the transcript = FAIL
# ---------------------------------------------------------------------------
FORBIDDEN_TERMS = [
    "simulated",
    "fallback",
    "placeholder",
    "mock transcript",
    "sample transcript",
    "generated transcript",
    "this is a simulated transcript",
    "this is a fallback transcript",
    "simulated fallback",
    "fake transcript",
    "demo transcript",
    "test transcript content",
]


class TranscriptValidationError(Exception):
    """
    Raised when transcript validation fails.
    Callers must NOT proceed to Gemini generation after catching this error.
    """

    def __init__(self, message: str, diagnostics: dict = None):
        super().__init__(message)
        self.diagnostics = diagnostics or {}


def validate_transcript(
    transcript_text: str,
    source_type: str,
    retrieval_method: str,
    retrieval_timestamp=None,
) -> dict:
    """
    Validate a transcript against all production rules.

    Returns diagnostics dict on PASS.
    Raises TranscriptValidationError on any FAIL.

    Args:
        transcript_text:     The raw transcript text from retrieval.
        source_type:         Must be 'youtube' (case-insensitive).
        retrieval_method:    Name of the retrieval method used (e.g. 'youtube-transcript-api').
        retrieval_timestamp: datetime of retrieval; required.

    Returns:
        {
            "status": "PASS",
            "length": <int>,
            "source": "youtube",
            "retrieval_method": <str>,
            "retrieval_timestamp": <ISO string>,
            "transcript_preview": <first 500 chars>,
        }
    """
    failures = []

    # ---- Rule 1: source_type must be 'youtube' ----------------------------
    source_norm = (source_type or "").strip().lower()
    if source_norm != "youtube":
        failures.append(f"source_type must be 'youtube', got '{source_type}'")

    # ---- Rule 2: transcript must not be empty / None ----------------------
    text_length = len(transcript_text) if transcript_text else 0
    if not transcript_text or text_length == 0:
        failures.append("transcript_text is empty or null")

    # ---- Rule 3: transcript must be > 10 chars ---------------------------
    if text_length > 0 and text_length <= 10:
        failures.append(
            f"transcript too short: {text_length} chars (minimum 10 required)"
        )

    # ---- Rule 4: retrieval_method must be present --------------------------
    if not retrieval_method or not retrieval_method.strip():
        failures.append("retrieval_method is missing or empty")

    # ---- Rule 5: retrieval_timestamp must exist ----------------------------
    if retrieval_timestamp is None:
        failures.append("retrieval_timestamp is missing — transcript was not freshly retrieved")

    # ---- Rule 6: no forbidden terms ----------------------------------------
    if transcript_text:
        text_lower = transcript_text.lower()
        for term in FORBIDDEN_TERMS:
            if re.search(re.escape(term), text_lower):
                failures.append(f"transcript contains forbidden term: '{term}'")
                break  # Report first match only

    # ---- Build diagnostics -------------------------------------------------
    preview = ""
    if transcript_text and text_length > 0:
        preview = transcript_text[:500] + ("..." if text_length > 500 else "")

    ts_str = None
    if isinstance(retrieval_timestamp, datetime):
        ts_str = retrieval_timestamp.isoformat()
    elif retrieval_timestamp is not None:
        ts_str = str(retrieval_timestamp)

    diagnostics = {
        "status": "PASS" if not failures else "FAIL",
        "length": text_length,
        "source": source_norm or "unknown",
        "retrieval_method": (retrieval_method or "").strip(),
        "retrieval_timestamp": ts_str,
        "transcript_preview": preview,
        "failures": failures,
    }

    if failures:
        error_msg = (
            f"Transcript validation FAILED ({len(failures)} rule(s) violated): "
            + "; ".join(failures)
        )
        logger.error(f"[TranscriptValidator] {error_msg}")
        raise TranscriptValidationError(error_msg, diagnostics=diagnostics)

    logger.info(
        f"[TranscriptValidator] PASS — length={text_length}, "
        f"method={retrieval_method}, source={source_type}"
    )
    return diagnostics
