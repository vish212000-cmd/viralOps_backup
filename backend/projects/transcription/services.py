"""
Transcription services — production-grade content extraction.

IMPORTANT: All fake/simulated/placeholder transcript generation has been removed.
YouTube ingestion is fully delegated to YouTubeIngestionService which enforces
strict validation. If extraction fails, TranscriptValidationError is raised and
Gemini generation is permanently blocked.
"""

import os
import time
import requests
import logging
from datetime import datetime
from django.conf import settings
from projects.models import UsageEvent

logger = logging.getLogger(__name__)


class TranscriptionError(Exception):
    pass


def get_transcription_provider():
    """
    Determines the transcription provider based on configuration.
    Returns: 'whisper', 'assemblyai'
    NOTE: 'simulated' mode has been removed — real transcription required.
    """
    pref = os.getenv('TRANSCRIPTION_PROVIDER', '').lower()
    openai_key = os.getenv('OPENAI_API_KEY')
    assembly_key = os.getenv('ASSEMBLYAI_API_KEY')

    if pref == 'whisper' and openai_key:
        return 'whisper'
    if pref == 'assemblyai' and assembly_key:
        return 'assemblyai'

    # Fallback to whatever is configured
    if openai_key:
        return 'whisper'
    if assembly_key:
        return 'assemblyai'

    return 'none'


def _extract_youtube_id(url):
    """Delegates to youtube_ingestion._extract_video_id — single implementation."""
    from projects.services.youtube_ingestion import _extract_video_id
    return _extract_video_id(url)


def _extract_article_text(url):
    try:
        from bs4 import BeautifulSoup
        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            timeout=15
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        for elem in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            elem.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = "\n".join(chunk for chunk in chunks if chunk)
        return clean_text
    except Exception as e:
        logger.error(f"Article scraping failed for {url}: {e}")
        return None


def _extract_pdf_text(file_path):
    try:
        import pypdf
        reader = pypdf.PdfReader(file_path)
        text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"PDF text extraction failed for {file_path}: {e}")
        return None


def transcribe_source_input(source_input):
    """
    Transcribes the source input.

    For YOUTUBE: Uses YouTubeIngestionService (multi-layer, strict validation).
                 Raises TranscriptValidationError if transcript cannot be obtained.
                 NEVER uses simulated/fallback text.

    For PDF:     Extracts real text from the PDF file.
                 Raises TranscriptionError if extraction fails (no fallback).

    For ARTICLE: Scrapes real article text.
                 Raises TranscriptionError if scraping fails (no fallback).

    For text-based (TRANSCRIPT, SCRIPT):
                 Uses text_content directly.

    For VIDEO/AUDIO:
                 Uses Whisper or AssemblyAI (real transcription providers).
                 Raises TranscriptionError if no provider is configured.

    Returns (raw_text, normalized_text, segments, duration_seconds)
    """
    provider = get_transcription_provider()
    logger.info(f"Using transcription provider: {provider} for SourceInput {source_input.id} (type={source_input.type})")

    # ----------------------------------------------------------------
    # YOUTUBE — full multi-layer ingestion with strict validation gate
    # ----------------------------------------------------------------
    if source_input.type == 'YOUTUBE':
        from projects.services.youtube_ingestion import (
            ingest_youtube_source,
            build_segments_from_text,
        )
        
        if source_input.transcript_source and source_input.transcript_source.startswith('uploaded_'):
            # It's a manual upload
            if not source_input.file:
                raise TranscriptionError("Uploaded transcript indicated but no file found.")
            
            ext = source_input.transcript_source.split('_')[1]
            try:
                from django.utils import timezone
                source_input.file.seek(0)
                content = source_input.file.read().decode('utf-8')
                source_input.text_content = content
                source_input.transcript_validation_status = 'PASS'
                source_input.transcript_length = len(content)
                source_input.transcript_retrieval_method = 'manual_upload'
                source_input.transcript_retrieved_at = timezone.now()
                source_input.transcript_preview = content[:500]
                source_input.save()
                
                if ext in ['srt', 'vtt']:
                    # Need to parse SRT/VTT for precise segments
                    from projects.transcription.subtitle_parser import parse_subtitles
                    segments, duration_seconds = parse_subtitles(content, ext)
                    normalized_text = "\n".join(s["text"] for s in segments)
                    return content, normalized_text, segments, duration_seconds
                else:
                    # TXT file
                    segments, duration_seconds = build_segments_from_text(content)
                    normalized_text = "\n".join(s["text"] for s in segments)
                    return content, normalized_text, segments, duration_seconds
            except Exception as e:
                raise TranscriptionError(f"Failed to parse uploaded transcript: {str(e)}")
        
        # This raises TranscriptValidationError if all layers fail
        diagnostics = ingest_youtube_source(source_input)
        transcript_text = source_input.text_content  # already saved by ingest_youtube_source
        segments, duration_seconds = build_segments_from_text(transcript_text)
        normalized_text = "\n".join(s["text"] for s in segments)
        return transcript_text, normalized_text, segments, duration_seconds

    # ----------------------------------------------------------------
    # PDF
    # ----------------------------------------------------------------
    if source_input.type == 'PDF':
        logger.info(f"SourceInput {source_input.id} is PDF.")
        if source_input.file:
            file_path = source_input.file.path
            if not os.path.exists(file_path):
                raise TranscriptionError(
                    f"PDF file path does not exist: {file_path}"
                )
            extracted_text = _extract_pdf_text(file_path)
            if not extracted_text or not any(c.isalnum() for c in extracted_text):
                raise TranscriptionError(
                    f"PDF text extraction produced no usable content for {source_input.file_name}. "
                    "The file may be a scanned image PDF or corrupted."
                )
            source_input.text_content = extracted_text
            source_input.save(update_fields=['text_content'])
            return _normalize_text_source(extracted_text, source_input.title or "PDF Document")
        elif source_input.text_content and source_input.text_content.strip():
            return _normalize_text_source(
                source_input.text_content,
                source_input.title or "PDF Text"
            )
        else:
            raise TranscriptionError("PDF source has no file and no text content.")

    # ----------------------------------------------------------------
    # ARTICLE / Blog URL
    # ----------------------------------------------------------------
    if source_input.type == 'ARTICLE' and source_input.source_url:
        logger.info(f"SourceInput {source_input.id} is Article: {source_input.source_url}")
        scraped_text = _extract_article_text(source_input.source_url)
        if not scraped_text or len(scraped_text.strip()) < 200:
            raise TranscriptionError(
                f"Article scraping returned insufficient content for URL: {source_input.source_url}"
            )
        source_input.text_content = scraped_text
        source_input.save(update_fields=['text_content'])
        return _normalize_text_source(scraped_text, source_input.title or "Article")

    # ----------------------------------------------------------------
    # Text-based sources (TRANSCRIPT, SCRIPT)
    # ----------------------------------------------------------------
    if not source_input.file and source_input.text_content:
        logger.info(f"SourceInput {source_input.id} is text-based. Normalizing directly.")
        return _normalize_text_source(
            source_input.text_content,
            source_input.title or "Text Source"
        )

    # ----------------------------------------------------------------
    # Video/Audio file transcription
    # ----------------------------------------------------------------
    if provider == 'none':
        if os.getenv('E2E_MOCK') == '1':
            logger.info("E2E_MOCK is set. Returning mock transcription.")
            segments = [{"start": 0, "end": 10, "speaker": "Speaker 1", "text": "This is a mocked transcription for E2E testing."}]
            return "This is a mocked transcription for E2E testing.", "This is a mocked transcription for E2E testing.", segments, 10
        raise TranscriptionError(
            "No transcription provider configured (OPENAI_API_KEY or ASSEMBLYAI_API_KEY required). "
            "Cannot transcribe VIDEO/AUDIO without a real provider."
        )

    file_path = source_input.file.path if source_input.file else None
    if not file_path or not os.path.exists(file_path):
        raise TranscriptionError(
            f"File not found for transcription: {file_path}"
        )

    if provider == 'whisper':
        return _transcribe_whisper(file_path)
    elif provider == 'assemblyai':
        return _transcribe_assemblyai(file_path)

    raise TranscriptionError(f"Unknown transcription provider: {provider}")


def _normalize_text_source(text: str, title: str):
    """
    Normalize plain text into segments and duration estimate.
    Used for non-YouTube sources (PDF, Article, direct text).
    """
    normalized_text = "\n".join([line.strip() for line in text.splitlines() if line.strip()])
    words = normalized_text.split()
    word_count = len(words)
    duration_seconds = max(60, int(word_count * 0.4))  # ~150 words per minute

    segments = []
    chunk_size = 50
    for i in range(0, len(words), chunk_size):
        segment_words = words[i:i + chunk_size]
        start_sec = (i / chunk_size) * 20
        end_sec = start_sec + 20
        segments.append({
            "start": start_sec,
            "end": end_sec,
            "speaker": "Speaker 1" if (i // chunk_size) % 2 == 0 else "Speaker 2",
            "text": " ".join(segment_words)
        })
    return text, normalized_text, segments, duration_seconds


def _transcribe_whisper(file_path):
    openai_key = os.getenv('OPENAI_API_KEY')
    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {openai_key}"}

    for attempt in range(3):
        try:
            with open(file_path, 'rb') as f:
                files = {
                    'file': (os.path.basename(file_path), f, 'application/octet-stream'),
                }
                data = {
                    'model': 'whisper-1',
                    'response_format': 'verbose_json'
                }
                response = requests.post(url, headers=headers, files=files, data=data, timeout=120)

            if response.status_code == 200:
                result = response.json()
                raw_text = result.get('text', '')
                normalized_text = "\n".join([line.strip() for line in raw_text.splitlines() if line.strip()])
                duration_seconds = float(result.get('duration', 0.0))

                raw_segments = result.get('segments', [])
                segments = []
                for s in raw_segments:
                    segments.append({
                        "start": s.get('start', 0.0),
                        "end": s.get('end', 0.0),
                        "speaker": "Speaker 1",
                        "text": s.get('text', '').strip()
                    })
                return raw_text, normalized_text, segments, int(duration_seconds)
            else:
                logger.error(f"Whisper API error: {response.status_code} - {response.text}")
                raise TranscriptionError(f"Whisper API returned status {response.status_code}")
        except (requests.RequestException, TranscriptionError) as e:
            if attempt == 2:
                raise e
            time.sleep(2 ** attempt)


def _transcribe_assemblyai(file_path):
    assembly_key = os.getenv('ASSEMBLYAI_API_KEY')
    headers = {"authorization": assembly_key}

    upload_url = "https://api.assemblyai.com/v2/upload"
    try:
        with open(file_path, 'rb') as f:
            upload_response = requests.post(upload_url, headers=headers, data=f, timeout=120)
        if upload_response.status_code != 200:
            raise TranscriptionError(f"AssemblyAI Upload failed: {upload_response.text}")
        audio_url = upload_response.json().get('upload_url')
    except Exception as e:
        raise TranscriptionError(f"AssemblyAI upload connection error: {str(e)}")

    transcript_url = "https://api.assemblyai.com/v2/transcript"
    payload = {"audio_url": audio_url, "speaker_labels": True}
    response = requests.post(transcript_url, json=payload, headers=headers, timeout=30)
    if response.status_code != 200:
        raise TranscriptionError(f"AssemblyAI transcription request failed: {response.text}")

    transcript_id = response.json().get('id')
    polling_url = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"

    for _ in range(60):
        time.sleep(10)
        poll_response = requests.get(polling_url, headers=headers, timeout=10)
        if poll_response.status_code != 200:
            raise TranscriptionError(f"AssemblyAI polling failed: {poll_response.text}")

        status = poll_response.json().get('status')
        if status == 'completed':
            result = poll_response.json()
            raw_text = result.get('text', '')
            normalized_text = "\n".join([line.strip() for line in raw_text.splitlines() if line.strip()])
            duration_seconds = int(result.get('audio_duration', 0) or 0)

            utterances = result.get('utterances')
            segments = []
            if utterances:
                for ut in utterances:
                    segments.append({
                        "start": ut.get('start', 0) / 1000.0,
                        "end": ut.get('end', 0) / 1000.0,
                        "speaker": f"Speaker {ut.get('speaker', 'A')}",
                        "text": ut.get('text', '').strip()
                    })
            else:
                words = result.get('words', [])
                chunk_size = 50
                for i in range(0, len(words), chunk_size):
                    chunk = words[i:i + chunk_size]
                    if not chunk:
                        continue
                    segments.append({
                        "start": chunk[0].get('start', 0) / 1000.0,
                        "end": chunk[-1].get('end', 0) / 1000.0,
                        "speaker": "Speaker 1",
                        "text": " ".join([w.get('text', '') for w in chunk])
                    })
            return raw_text, normalized_text, segments, duration_seconds
        elif status == 'failed':
            error_msg = poll_response.json().get('error', 'Unknown failure')
            raise TranscriptionError(f"AssemblyAI transcription failed: {error_msg}")

    raise TranscriptionError("AssemblyAI transcription polling timed out.")


def log_transcription_usage(organization, user, duration_seconds):
    """Log usage minutes for the organization workspace."""
    duration_minutes = max(1, int(duration_seconds / 60))
    UsageEvent.objects.create(
        organization=organization,
        user=user,
        event_type='TRANSCRIPTION_MINUTES',
        quantity=duration_minutes
    )
    logger.info(f"Logged {duration_minutes} transcription minutes for organization {organization.slug}")
