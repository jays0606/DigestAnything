"""Test 6: YouTube transcript extraction."""
import os, json
from youtube_transcript_api import YouTubeTranscriptApi

# Demo video from spec
VIDEO_URL = "https://www.youtube.com/watch?v=kwSVtQ7dziU"
VIDEO_ID = "kwSVtQ7dziU"

print(f"=== YouTube Transcript: {VIDEO_URL} ===")

try:
    ytt = YouTubeTranscriptApi()
    transcript = ytt.fetch(VIDEO_ID, languages=["en", "ko"])
    full_text = " ".join([t.text for t in transcript])
    print(f"Segments: {len(transcript)}")
    print(f"Total chars: {len(full_text)}")
    print(f"First 300 chars: {full_text[:300]}...")
    assert len(transcript) > 10, "Too few transcript segments"
    assert len(full_text) > 500, "Transcript too short"

    # Save for other tests
    OUT_DIR = os.path.join(os.path.dirname(__file__), "samples")
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "youtube_transcript.json"), "w") as f:
        json.dump({"video_id": VIDEO_ID, "segments": [{"text": t.text, "start": t.start, "duration": t.duration} for t in transcript[:20]], "full_text": full_text[:3000]}, f, indent=2)

    print("\nTest 6 PASSED")
except Exception as e:
    print(f"\nTest 6 FAILED: {e}")
    print("(This may fail if video has no captions or is geo-restricted)")
    raise
