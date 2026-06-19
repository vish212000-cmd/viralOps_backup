import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "viralops.settings")
django.setup()

from projects.services.youtube_ingestion import _retrieve_via_audio_transcription

print("Starting audio transcription fallback test...")
try:
    text, method = _retrieve_via_audio_transcription("https://www.youtube.com/watch?v=jNQXAC9IVRw")
    print(f"SUCCESS: {method}")
    print(f"Length: {len(text)}")
    print(f"Preview: {text[:200]}")
except Exception as e:
    print(f"FAILED: {e}")
