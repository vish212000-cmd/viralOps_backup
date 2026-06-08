"""
YouTubeIngestionService — Production-grade multi-layer YouTube transcript retrieval.

Layer 1: youtube-transcript-api  (official)
Layer 2: yt-dlp subtitle extraction
Layer 3: yt-dlp auto-generated subtitles
Layer 4: User-supplied manual transcript (text_content field)

If ALL layers fail → raises TranscriptValidationError.
NEVER fabricates, simulates, or generates placeholder transcript text.
"""

import logging
import subprocess
import sys
import json
import re
import os
import tempfile
from django.utils import timezone

from projects.services.transcript_validator import (
    TranscriptValidationError,
    validate_transcript,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_video_id(url: str) -> str | None:
    """Extract 11-char YouTube video ID from any YouTube URL format."""
    patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?(?:.*&)?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        # Non-www forms (e.g., https://youtube.com/watch?v=...)
        r'(?:https?://)?youtube\.com/watch\?(?:.*&)?v=([a-zA-Z0-9_-]{6,11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def _join_transcript_pieces(pieces: list[str]) -> str:
    """Join transcript text pieces into a single clean string."""
    return " ".join(p.strip() for p in pieces if p.strip())


# ---------------------------------------------------------------------------
# Layer 1: youtube-transcript-api
# ---------------------------------------------------------------------------

def _retrieve_via_transcript_api(video_id: str) -> tuple[str, str]:
    """
    Attempt retrieval via youtube-transcript-api.
    Returns (transcript_text, method_name).
    Raises on failure.
    """
    from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

    logger.info(f"[YT Layer 1] Attempting youtube-transcript-api for video_id={video_id}")
    
    # Try English first, then any available language
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    
    transcript = None
    try:
        transcript = transcript_list.find_manually_created_transcript(['en', 'en-US', 'en-GB'])
        method = "youtube-transcript-api/manual-en"
    except Exception:
        try:
            transcript = transcript_list.find_generated_transcript(['en', 'en-US', 'en-GB'])
            method = "youtube-transcript-api/auto-en"
        except Exception:
            # Try first available language and translate to english
            for t in transcript_list:
                try:
                    transcript = t.translate('en')
                    method = f"youtube-transcript-api/{t.language_code}-translated-to-en"
                except Exception:
                    transcript = t
                    method = f"youtube-transcript-api/{t.language_code}"
                break

    if transcript is None:
        raise Exception("No transcript tracks found via youtube-transcript-api")

    entries = transcript.fetch()
    pieces = [e.get('text', '').strip() for e in entries if e.get('text', '').strip()]
    text = _join_transcript_pieces(pieces)

    if len(text) < 100:
        raise Exception(f"Retrieved transcript is too short ({len(text)} chars) via transcript-api")

    logger.info(f"[YT Layer 1] SUCCESS — {len(text)} chars via {method}")
    return text, method


# ---------------------------------------------------------------------------
# Layer 2 & 3: yt-dlp subtitle extraction
# ---------------------------------------------------------------------------

def _retrieve_via_ytdlp(url: str) -> tuple[str, str]:
    """
    Attempt retrieval via yt-dlp (manual subtitles first, then auto-generated).
    Returns (transcript_text, method_name).
    Raises on failure.
    """
    logger.info(f"[YT Layer 2/3] Attempting yt-dlp subtitle extraction for {url}")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Try manual subtitles first (Layer 2)
        for sub_arg, method_label in [
            ("--write-subs", "yt-dlp/manual-subs"),
            ("--write-auto-subs", "yt-dlp/auto-subs"),
        ]:
            try:
                cmd = [
                    sys.executable, "-m", "yt_dlp",
                    "--skip-download",
                    sub_arg,
                    "--sub-langs", "en,te-orig,hi,en-US",
                    "--sub-format", "json3",
                    "--output", os.path.join(tmpdir, "%(id)s.%(ext)s"),
                    url,
                    "--no-playlist",
                    "--quiet",
                ]
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=120
                )

                # Find any downloaded .json3 subtitle file
                for fname in os.listdir(tmpdir):
                    if fname.endswith(".json3") or fname.endswith(".vtt"):
                        fpath = os.path.join(tmpdir, fname)
                        text = _parse_subtitle_file(fpath)
                        if text and len(text) > 100:
                            logger.info(f"[YT Layer 2/3] SUCCESS — {len(text)} chars via {method_label}")
                            return text, method_label

            except subprocess.TimeoutExpired:
                logger.warning(f"[YT Layer 2/3] yt-dlp timed out for {method_label}")
                continue
            except FileNotFoundError:
                logger.warning("[YT Layer 2/3] yt-dlp not found in PATH, skipping")
                raise Exception("yt-dlp not available")
            except Exception as e:
                logger.warning(f"[YT Layer 2/3] {method_label} failed: {e}")
                continue

    raise Exception("yt-dlp subtitle extraction failed — no usable subtitle file found")


def _parse_subtitle_file(fpath: str) -> str:
    """Parse a .json3 or .vtt subtitle file into plain text.
    VTT parsing delegates to transcription.subtitle_parser (single implementation).
    """
    try:
        if fpath.endswith(".json3"):
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            events = data.get("events", [])
            pieces = []
            for ev in events:
                for seg in ev.get("segs", []):
                    t = seg.get("utf8", "").strip()
                    if t and t != "\n":
                        pieces.append(t)
            return _join_transcript_pieces(pieces)
        elif fpath.endswith(".vtt"):
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            # Delegate to canonical subtitle parser
            from projects.transcription.subtitle_parser import parse_subtitles
            try:
                segments, _ = parse_subtitles(content, "vtt")
                return " ".join(s["text"] for s in segments if s.get("text"))
            except Exception:
                # Fallback: strip VTT headers manually if parser fails
                lines = content.splitlines()
                text_lines = [
                    re.sub(r"<[^>]+>", "", line.strip())
                    for line in lines
                    if line.strip()
                    and not line.strip().startswith("WEBVTT")
                    and "-->" not in line
                    and not re.match(r"^\d+$", line.strip())
                ]
                return " ".join(t for t in text_lines if t)
    except Exception as e:
        logger.warning(f"[YT SubtitleParser] Failed to parse {fpath}: {e}")
    return ""


# ---------------------------------------------------------------------------
# Layer 4: User-supplied manual transcript
# ---------------------------------------------------------------------------

def _retrieve_from_manual_input(source_input) -> tuple[str, str]:
    """
    Use the text_content field if the user pre-supplied a manual transcript.
    This is only valid if the field was set BEFORE processing started
    (e.g. user pasted their own transcript).
    """
    text = (source_input.text_content or "").strip()
    if text and len(text) > 1000:
        logger.info(f"[YT Layer 4] Using user-supplied manual transcript ({len(text)} chars)")
        return text, "manual-user-supplied"
    raise Exception(
        f"No usable manual transcript supplied (length={len(text)})"
    )


# ---------------------------------------------------------------------------
# Public API — ingest YouTube source
# ---------------------------------------------------------------------------

def ingest_youtube_source(source_input) -> dict:
    """
    Main entry point for YouTube ingestion.

    Tries each retrieval layer in order. If all fail, raises TranscriptValidationError.
    On success, returns validated diagnostics dict and updates source_input fields.

    Never generates, simulates, or fabricates transcript content.

    Returns:
        diagnostics dict from validate_transcript()

    Side-effects:
        Updates source_input fields:
          - text_content
          - transcript_source
          - transcript_length
          - transcript_validation_status
          - transcript_retrieval_method
          - transcript_retrieved_at
          - transcript_preview
    """
    url = source_input.source_url
    video_id = _extract_video_id(url)

    if not video_id:
        raise TranscriptValidationError(
            f"Could not extract video ID from YouTube URL: {url}",
            diagnostics={"status": "FAIL", "failures": ["Invalid YouTube URL"]}
        )

    logger.info(f"[YouTubeIngestion] Starting multi-layer retrieval for video_id={video_id}")

    transcript_text = None
    retrieval_method = None
    last_error = None

    # --- Layer 1 ---
    try:
        transcript_text, retrieval_method = _retrieve_via_transcript_api(video_id)
    except Exception as e:
        last_error = e
        logger.warning(f"[YouTubeIngestion] Layer 1 failed: {e}")

    # --- Layer 2 & 3 ---
    if not transcript_text:
        try:
            transcript_text, retrieval_method = _retrieve_via_ytdlp(url)
        except Exception as e:
            last_error = e
            logger.warning(f"[YouTubeIngestion] Layer 2/3 failed: {e}")

    # --- Layer 4 ---
    if not transcript_text:
        try:
            transcript_text, retrieval_method = _retrieve_from_manual_input(source_input)
        except Exception as e:
            last_error = e
            logger.warning(f"[YouTubeIngestion] Layer 4 failed: {e}")

    # --- ALL LAYERS FAILED ---
    if not transcript_text:
        error_msg = (
            f"All transcript retrieval layers exhausted for video {url}. "
            f"Last error: {last_error}. "
            "Ingestion FAILED — Gemini generation blocked."
        )
        logger.error(f"[YouTubeIngestion] {error_msg}")
        raise TranscriptValidationError(
            error_msg,
            diagnostics={
                "status": "FAIL",
                "length": 0,
                "source": "youtube",
                "retrieval_method": None,
                "retrieval_timestamp": None,
                "transcript_preview": "",
                "failures": [str(last_error)],
            }
        )

    # --- VALIDATE the retrieved transcript ---
    retrieval_timestamp = timezone.now()
    diagnostics = validate_transcript(
        transcript_text=transcript_text,
        source_type="youtube",
        retrieval_method=retrieval_method,
        retrieval_timestamp=retrieval_timestamp,
    )

    # --- Persist diagnostics to source_input ---
    source_input.text_content = transcript_text
    source_input.transcript_source = "youtube"
    source_input.transcript_length = diagnostics["length"]
    source_input.transcript_validation_status = diagnostics["status"]
    source_input.transcript_retrieval_method = retrieval_method
    source_input.transcript_retrieved_at = retrieval_timestamp
    source_input.transcript_preview = diagnostics["transcript_preview"]
    source_input.save(update_fields=[
        "text_content",
        "transcript_source",
        "transcript_length",
        "transcript_validation_status",
        "transcript_retrieval_method",
        "transcript_retrieved_at",
        "transcript_preview",
    ])

    logger.info(
        f"[YouTubeIngestion] PASS — video={video_id}, "
        f"length={diagnostics['length']}, method={retrieval_method}"
    )
    return diagnostics


def build_segments_from_text(transcript_text: str) -> tuple[list, int]:
    """
    Build segment list and duration estimate from plain transcript text.
    Delegates to transcription.services._normalize_text_source — single implementation.
    Used downstream by tasks.py when creating TranscriptRecord.
    """
    from projects.transcription.services import _normalize_text_source
    _raw, _normalized, segments, duration_seconds = _normalize_text_source(
        transcript_text, "YouTube Transcript"
    )
    return segments, duration_seconds
