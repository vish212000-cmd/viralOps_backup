import sys
import os
import django
import json
import time

sys.path.append(r'c:\personal\projects\viralOps\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viralops.settings')
django.setup()

from django.contrib.auth import get_user_model
from organizations.models import Organization, Membership
from projects.models import Project, SourceInput, TranscriptRecord, Moment, GeneratedAsset, TranscriptSegment
from projects.transcription.services import transcribe_source_input
from projects.services.moment_detection_service import detect_moments
from projects.ai_service import generate_social_assets

def run_real_validation():
    print("--- Starting REAL Validation ---")
    User = get_user_model()
    user, _ = User.objects.get_or_create(username="real_validator", email="real@viralops.com")
    org, _ = Organization.objects.get_or_create(name="Real Org", slug="real-org")
    Membership.objects.get_or_create(user=user, organization=org, role="ADMIN")
    project, _ = Project.objects.get_or_create(organization=org, name="Real Intelligence Test")
    
    SourceInput.objects.filter(project=project).delete()
    TranscriptRecord.objects.filter(source_input__project=project).delete()
    Moment.objects.filter(project=project).delete()
    GeneratedAsset.objects.filter(project=project).delete()
    
    video_url = "https://www.youtube.com/watch?v=cXdYzOulY1o"
    print(f"Creating source for {video_url}")
    
    source_input = SourceInput.objects.create(
        project=project,
        type='YOUTUBE',
        source_url=video_url,
        status='PROCESSING'
    )
    
    # Wait a few seconds to avoid immediate rate limit if we just hit something
    time.sleep(2)
    
    print("1. Retrieving actual transcript via YouTube Ingestion Service...")
    try:
        transcript_text, normalized_text, segments, duration_seconds = transcribe_source_input(source_input)
    except Exception as e:
        print(f"FAIL: Transcript retrieval failed: {e}")
        return
        
    print(f"Transcript Length: {len(transcript_text)}")
    print("2/3. Generating transcript segments...")
    record = TranscriptRecord.objects.create(
        source_input=source_input,
        raw_text=transcript_text,
        normalized_text=normalized_text,
        segments=segments
    )
    
    for i, seg in enumerate(segments):
        TranscriptSegment.objects.create(
            transcript_record=record,
            start_time=seg['start'],
            end_time=seg['end'],
            text=seg['text'],
            speaker=seg.get('speaker', 'SPEAKER_00'),
            segment_index=i
        )
    print(f"Saved {len(segments)} segments.")
    
    print("4/5. Generating moments and viral scores via real Gemini API...")
    try:
        saved_moments = detect_moments(project, source_input, record)
        print(f"Detected {len(saved_moments)} moments.")
    except Exception as e:
        print(f"FAIL: detect_moments failed: {e}")
        return
        
    moments_db = list(Moment.objects.filter(project=project).order_by('-score'))
    if not moments_db:
        print("FAIL: No moments generated.")
        return
        
    print("6. Selecting top 5 moments...")
    top_moments = moments_db[:5]
    
    results = []
    
    print("7/8. Generating assets for each moment using real Gemini API...")
    for idx, m in enumerate(top_moments):
        print(f"\nProcessing Moment {idx+1}/{len(top_moments)}: {m.title} (Score: {m.score})")
        
        # Add slight delay to avoid Gemini rate limits
        time.sleep(3)
        try:
            assets = generate_social_assets(
                title=m.title,
                source_type='YOUTUBE',
                content_text=m.excerpt
            )
            
            results.append({
                "timestamp": f"{m.start_time} - {m.end_time}",
                "category": m.category,
                "score": m.score,
                "excerpt": m.excerpt,
                "title": m.title,
                "hook": assets.get('hooks', [''])[0] if assets.get('hooks') else "N/A",
                "caption": assets.get('captions', [''])[0] if assets.get('captions') else "N/A"
            })
            print("  -> Assets generated successfully")
        except Exception as e:
            print(f"  -> FAIL generating assets: {e}")
    
    print("\n--- SIDE-BY-SIDE COMPARISON ---")
    for idx, res in enumerate(results):
        print(f"\n### Moment {idx+1}")
        print(f"Timestamp: {res['timestamp']}")
        print(f"Category: {res['category']}")
        print(f"Viral Score: {res['score']}")
        print(f"Title: {res['title']}")
        print(f"Excerpt/Reason: {res['excerpt'][:200]}...")
        print(f"Generated Hook: {res['hook']}")
        print(f"Generated Caption: {res['caption']}")

if __name__ == '__main__':
    run_real_validation()
