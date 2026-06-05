from youtube_transcript_api import YouTubeTranscriptApi
import sys

ids = ['sBws8MSXN7A', 'w7ejDZ8SWv8', 'tPeX772wN90', 'dQw4w9WgXcQ', '2e1z_31D38k', 'jNQXAC9IVRw', 'g3j9782Gg10']
for i in ids:
    try:
        t = YouTubeTranscriptApi.get_transcript(i)
        print(f"ID: {i} -> SUCCESS, segments: {len(t)}")
    except Exception as e:
        print(f"ID: {i} -> FAILED, error: {type(e).__name__} {str(e)}")
