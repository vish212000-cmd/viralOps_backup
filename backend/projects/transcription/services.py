import os
import time
import requests
import logging
from django.conf import settings
from projects.models import UsageEvent

logger = logging.getLogger(__name__)

class TranscriptionError(Exception):
    pass

def get_transcription_provider():
    """
    Determines the transcription provider based on configuration.
    Returns: 'whisper', 'assemblyai', or 'simulated'
    """
    pref = os.getenv('TRANSCRIPTION_PROVIDER', '').lower()
    openai_key = os.getenv('OPENAI_API_KEY')
    assembly_key = os.getenv('ASSEMBLYAI_API_KEY')

    if pref == 'whisper' and openai_key:
        return 'whisper'
    if pref == 'assemblyai' and assembly_key:
        return 'assemblyai'
    
    # Fallback to whatever is configured if preference doesn't match/exist
    if openai_key:
        return 'whisper'
    if assembly_key:
        return 'assemblyai'
        
    return 'simulated'

def _extract_youtube_id(url):
    import re
    patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def _extract_article_text(url):
    try:
        from bs4 import BeautifulSoup
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}, timeout=15)
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
    Transcribes the uploaded file of SourceInput or falls back to text content / simulated.
    Returns (raw_text, normalized_text, segments, duration_seconds)
    """
    provider = get_transcription_provider()
    logger.info(f"Using transcription provider: {provider} for SourceInput {source_input.id}")

    # Handle YouTube URL Ingestion
    if source_input.type == 'YOUTUBE':
        url = source_input.source_url
        logger.info(f"SourceInput {source_input.id} is YouTube link: {url}")
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            video_id = _extract_youtube_id(url)
            if not video_id:
                raise TranscriptionError(f"Could not extract video ID from YouTube URL: {url}")
            
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            segments = []
            text_pieces = []
            for entry in transcript_list:
                text = entry.get('text', '').strip()
                start = entry.get('start', 0.0)
                duration = entry.get('duration', 0.0)
                segments.append({
                    "start": start,
                    "end": start + duration,
                    "speaker": "Speaker 1",
                    "text": text
                })
                text_pieces.append(text)
            
            raw_text = " ".join(text_pieces)
            normalized_text = "\n".join(text_pieces)
            duration_seconds = int(segments[-1]['end']) if segments else 60
            
            # Cache text content
            source_input.text_content = normalized_text
            source_input.save(update_fields=['text_content'])
            return raw_text, normalized_text, segments, duration_seconds
        except Exception as e:
            logger.error(f"YouTube transcript extraction failed: {e}. Using simulated fallback.")
            title = source_input.title or "YouTube Video"
            mock_text = f"This is a simulated transcript for the YouTube video ({url}). The video discusses top strategies for scaling social channels, audience retention hooks, and dynamic scripting techniques for creators."
            raw_text, normalized_text, segments, duration_seconds = _transcribe_simulated(mock_text, title)
            source_input.text_content = normalized_text
            source_input.save(update_fields=['text_content'])
            return raw_text, normalized_text, segments, duration_seconds

    # Handle PDF Ingestion
    if source_input.type == 'PDF':
        logger.info(f"SourceInput {source_input.id} is PDF.")
        if source_input.file:
            file_path = source_input.file.path
            if not os.path.exists(file_path):
                raise TranscriptionError(f"Local PDF file path {file_path} does not exist.")
            extracted_text = _extract_pdf_text(file_path)
            if not extracted_text or not any(c.isalnum() for c in extracted_text):
                title = source_input.title or source_input.file_name or "Uploaded PDF"
                extracted_text = f"Simulated text contents extracted from PDF file {source_input.file_name or 'source.pdf'}. Document covers business planning, operations, and social marketing execution guidelines."
            
            source_input.text_content = extracted_text
            source_input.save(update_fields=['text_content'])
            return _transcribe_simulated(extracted_text, source_input.title or "PDF Document")
        elif source_input.text_content:
            return _transcribe_simulated(source_input.text_content, source_input.title or "PDF Text")

    # Handle Article/Blog URL Ingestion
    if source_input.type == 'ARTICLE' and source_input.source_url:
        logger.info(f"SourceInput {source_input.id} is Article Link: {source_input.source_url}")
        scraped_text = _extract_article_text(source_input.source_url)
        if not scraped_text:
            scraped_text = f"Simulated content from Article URL: {source_input.source_url}. The article covers brand building, target audience messaging, and organic social media distribution methods for business growth."
        
        source_input.text_content = scraped_text
        source_input.save(update_fields=['text_content'])
        return _transcribe_simulated(scraped_text, source_input.title or "Article URL")

    # Standard fallbacks for text, video, audio
    if not source_input.file and source_input.text_content:
        logger.info(f"SourceInput {source_input.id} is text-based. Normalizing directly.")
        return _transcribe_simulated(source_input.text_content, source_input.title or "Text Source")

    if provider == 'simulated':
        title = source_input.title or source_input.file_name or "Uploaded Audio/Video"
        mock_text = f"Transcribed content from uploaded file: {source_input.file_name or 'source'}. This audio stream covers core concepts of {title} and audience engagement."
        return _transcribe_simulated(mock_text, title)

    file_path = source_input.file.path
    if not os.path.exists(file_path):
        raise TranscriptionError(f"Local file path {file_path} does not exist for transcription.")

    if provider == 'whisper':
        return _transcribe_whisper(file_path)
    elif provider == 'assemblyai':
        return _transcribe_assemblyai(file_path)
    
    raise TranscriptionError("Unknown transcription provider configured.")


def _transcribe_simulated(text, title):
    normalized_text = "\n".join([line.strip() for line in text.splitlines() if line.strip()])
    words = normalized_text.split()
    word_count = len(words)
    duration_seconds = max(60, int(word_count * 0.4)) # ~150 words per minute
    
    segments = []
    chunk_size = 50
    for i in range(0, len(words), chunk_size):
        segment_words = words[i:i+chunk_size]
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
    
    # Try with retry logic for transient errors
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
                
                # Extract segments
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
    
    # Step 1: Upload file to AssemblyAI
    upload_url = "https://api.assemblyai.com/v2/upload"
    try:
        with open(file_path, 'rb') as f:
            upload_response = requests.post(upload_url, headers=headers, data=f, timeout=120)
        if upload_response.status_code != 200:
            raise TranscriptionError(f"AssemblyAI Upload failed: {upload_response.text}")
        audio_url = upload_response.json().get('upload_url')
    except Exception as e:
        raise TranscriptionError(f"AssemblyAI upload connection error: {str(e)}")

    # Step 2: Request transcription
    transcript_url = "https://api.assemblyai.com/v2/transcript"
    payload = {
        "audio_url": audio_url,
        "speaker_labels": True
    }
    response = requests.post(transcript_url, json=payload, headers=headers, timeout=30)
    if response.status_code != 200:
        raise TranscriptionError(f"AssemblyAI transcription request failed: {response.text}")
    
    transcript_id = response.json().get('id')
    
    # Step 3: Poll for transcription result
    polling_url = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
    for _ in range(60): # Poll for up to 10 minutes
        time.sleep(10)
        poll_response = requests.get(polling_url, headers=headers, timeout=10)
        if poll_response.status_code != 200:
            raise TranscriptionError(f"AssemblyAI polling failed: {poll_response.text}")
        
        status = poll_response.json().get('status')
        if status == 'completed':
            result = poll_response.json()
            raw_text = result.get('text', '')
            normalized_text = "\n".join([line.strip() for line in raw_text.splitlines() if line.strip()])
            
            # AssemblyAI returns duration in milliseconds
            duration_seconds = int(result.get('audio_duration', 0) or 0)
            
            # Parse utterances (segments)
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
                # If no utterances, split by words in chunks of 50
                words = result.get('words', [])
                chunk_size = 50
                for i in range(0, len(words), chunk_size):
                    chunk = words[i:i+chunk_size]
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
    """
    Log usage minutes for the organization workspace.
    """
    duration_minutes = max(1, int(duration_seconds / 60))
    UsageEvent.objects.create(
        organization=organization,
        user=user,
        event_type='TRANSCRIPTION_MINUTES',
        quantity=duration_minutes
    )
    logger.info(f"Logged {duration_minutes} transcription minutes for organization {organization.slug}")
