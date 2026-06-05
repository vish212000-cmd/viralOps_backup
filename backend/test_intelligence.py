import sys
import os
import django
import json

# Setup Django environment
sys.path.append(r'c:\personal\projects\viralOps\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viralops.settings')
django.setup()

from django.contrib.auth import get_user_model
from organizations.models import Organization, Membership
from projects.models import Project, SourceInput, TranscriptRecord, Moment, GeneratedAsset, TranscriptSegment
from projects.transcription.services import transcribe_source_input
from projects.services.moment_detection_service import detect_moments
from projects.ai_service import generate_social_assets
from unittest.mock import patch

class MockResponse:
    def __init__(self, text):
        self.text = text

def mock_generate_content(*args, **kwargs):
    prompt = args[1] if len(args) > 1 else kwargs.get('contents', args[0][0] if isinstance(args[0], list) else args[0])
    if "DETECT VIRAL MOMENTS" in prompt or "moments" in prompt.lower():
        return MockResponse("""
[
  {
    "title": "The Titanium Design is Incredible",
    "start_time": "00:00:20",
    "end_time": "00:00:40",
    "score": 85,
    "category": "HOOK",
    "excerpt": "The design is absolutely incredible. Apple has really outdone themselves with the titanium finish."
  },
  {
    "title": "The 2000 Nits Screen",
    "start_time": "00:00:40",
    "end_time": "00:01:00",
    "score": 95,
    "category": "EDUCATIONAL",
    "excerpt": "But the real story here is the screen. This screen is the brightest we've ever tested on a phone, hitting nearly 2000 nits. When you use it outside, it's a game changer."
  },
  {
    "title": "Worth the Upgrade?",
    "start_time": "00:01:00",
    "end_time": "00:01:20",
    "score": 75,
    "category": "CTA",
    "excerpt": "To wrap up this review, if you have an older phone, this Apple device is worth the upgrade."
  }
]
        """)
    else:
        return MockResponse("""
{
  "hooks": ["This Apple phone will blow your mind!", "Why the new iPhone screen is a game changer."],
  "captions": ["The new titanium finish is beautiful. Check out our full review!", "2000 nits? That's insane. Here's why you need the new Apple screen."]
}
        """)
        
User = get_user_model()

@patch('google.generativeai.GenerativeModel.generate_content', side_effect=mock_generate_content)
def run_validation(mock_genai):
    print("--- Starting Validation ---")
    
    # 1. Setup Data
    user, _ = User.objects.get_or_create(username="validator", email="val@viralops.com")
    org, _ = Organization.objects.get_or_create(name="Val Org", slug="val-org")
    Membership.objects.get_or_create(user=user, organization=org, role="ADMIN")
    project, _ = Project.objects.get_or_create(organization=org, name="Intelligence Test")
    
    # Cleanup previous runs
    SourceInput.objects.filter(project=project).delete()
    TranscriptRecord.objects.filter(source_input__project=project).delete()
    Moment.objects.filter(project=project).delete()
    GeneratedAsset.objects.filter(project=project).delete()
    
    # 2. Ingest Real YouTube Transcript
    # Let's use a popular video (e.g. Marques Brownlee or a TED Talk). 
    # MKBHD review: "d_xLktWJ5xI" or TED: "8KkKuTCFvzI"
    video_url = "https://www.youtube.com/watch?v=u4ZoJKF_VuA" 
    
    mock_text = """
Welcome back to the channel. Today we're looking at the new Apple iPhone. 
The design is absolutely incredible. Apple has really outdone themselves with the titanium finish. 
But the real story here is the screen. This screen is the brightest we've ever tested on a phone, hitting nearly 2000 nits.
When you use it outside, it's a game changer. The camera is also top-notch, though the price is still very high.
To wrap up this review, if you have an older phone, this Apple device is worth the upgrade.
""" * 10

    source_input = SourceInput.objects.create(
        project=project,
        type='YOUTUBE',
        source_url=video_url,
        text_content=mock_text,
        status='PROCESSING'
    )
    
    print(f"Fetching transcript for {video_url}...")
    try:
        transcript_text, normalized_text, segments, duration_seconds = transcribe_source_input(source_input)
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return
        
    print(f"Transcript length: {len(transcript_text)}")
    
    # Create TranscriptRecord and Segments
    record = TranscriptRecord.objects.create(
        source_input=source_input,
        raw_text=transcript_text,
        normalized_text=normalized_text,
        segments=segments
    )
    
    # 3. Generate Segments
    for i, seg in enumerate(segments):
        TranscriptSegment.objects.create(
            transcript_record=record,
            start_time=seg['start'],
            end_time=seg['end'],
            text=seg['text'],
            speaker=seg.get('speaker', 'SPEAKER_00'),
            segment_index=i
        )
    print(f"Saved {TranscriptSegment.objects.filter(transcript_record=record).count()} segments.")
    
    # 4 & 5. Generate Moments & Scores & Rank
    print("Detecting moments via Gemini...")
    saved_moments = detect_moments(project, source_input, record)
    print(f"Detected {len(saved_moments)} moments.")
    
    moments_db = list(Moment.objects.filter(project=project).order_by('-score'))
    if not moments_db:
        print("FAIL: No moments generated.")
        return
        
    print("Top Ranked Moments:")
    for m in moments_db[:3]:
        print(f" - [{m.score}] {m.title} ({m.category}) | {m.start_time} - {m.end_time}")
        print(f"   Segments Count: {m.segments.count()}")
        
    top_moment = moments_db[0]
    other_moment = moments_db[-1] # lowest score moment
    
    # 6. Generate Assets from Top Moment
    print(f"\nGenerating assets for TOP moment: {top_moment.title}")
    top_assets = generate_social_assets(
        title=top_moment.title,
        source_type='ARTICLE',
        content_text=top_moment.excerpt
    )
    print(f"Top Moment Assets:\nHooks: {top_assets.get('hooks')}\nCaptions: {top_assets.get('captions')}")
    
    # 7. Generate Assets from a Different Moment
    print(f"\nGenerating assets for OTHER moment: {other_moment.title}")
    other_assets = generate_social_assets(
        title=other_moment.title,
        source_type='ARTICLE',
        content_text=other_moment.excerpt
    )
    print(f"Other Moment Assets:\nHooks: {other_assets.get('hooks')}\nCaptions: {other_assets.get('captions')}")
    
    # 11. Moment Search
    print("\nTesting Moment Search (keywords: 'apple' or 'phone' or 'screen' or 'review')...")
    search_query = "apple" 
    matches = []
    for m in moments_db:
        searchable = f"{m.title} {m.excerpt} {m.category}".lower()
        if search_query in searchable:
            matches.append(m.title)
    print(f"Search '{search_query}' found in: {matches}")
    
    print("\n--- Validation Complete ---")

if __name__ == '__main__':
    run_validation()
