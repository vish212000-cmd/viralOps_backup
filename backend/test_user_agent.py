from youtube_transcript_api import YouTubeTranscriptApi
import requests

video_id = 'dQw4w9WgXcQ'
try:
    tl = YouTubeTranscriptApi.list_transcripts(video_id)
    t = next(iter(tl))
    print("Found transcript:", t.language)
    
    # Update session headers with a browser user-agent
    t._http_client.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    })
    
    data = t.fetch()
    print("SUCCESS! Transcript length:", len(data))
    print("First segment:", data[0])
except Exception as e:
    print("Error:", type(e).__name__, str(e))
