from youtube_transcript_api import YouTubeTranscriptApi
import requests

video_id = 'dQw4w9WgXcQ'
try:
    tl = YouTubeTranscriptApi.list_transcripts(video_id)
    print("Fetched list successfully!")
    for t in tl:
        print("Language:", t.language, "Code:", t.language_code)
        url = t._url
        print("URL:", url)
        # Fetch with browser-like user agent
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        print("Status:", r.status_code, "Length:", len(r.text))
        print("Text snippet:", r.text[:200])
except Exception as e:
    print("Error:", type(e).__name__, str(e))
