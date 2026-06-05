from youtube_transcript_api import YouTubeTranscriptApi
import requests

video_id = 'dQw4w9WgXcQ'
try:
    tl = YouTubeTranscriptApi.list_transcripts(video_id)
    t = next(iter(tl))
    url = t._url
    session = t._http_client

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.youtube.com/",
        "Origin": "https://www.youtube.com"
    }

    for fmt in ['', 'json3', 'srv1', 'vtt']:
        test_url = url + f"&fmt={fmt}" if fmt else url
        r = session.get(test_url, headers=headers)
        print(f"Format: {fmt or 'default'} -> Status: {r.status_code}, Length: {len(r.content)}")
        if len(r.content) > 0:
            print("Snippet:", r.text[:200])
except Exception as e:
    print("Error:", e)
