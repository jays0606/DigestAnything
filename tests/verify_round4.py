"""Verify Round 4: Podcast.

Requires: backend on :8000 with /api/ingest working (Round 1 complete).
"""
import httpx
import json
import os
import sys

BASE = "http://localhost:8000"
TEST_URL = "https://www.anthropic.com/engineering/harness-design-long-running-apps"


def get_context():
    """Get context by ingesting test URL."""
    print("=== Getting context (ingest) ===")
    r = httpx.post(f"{BASE}/api/ingest", json={"source": TEST_URL}, timeout=90)
    assert r.status_code == 200, f"Ingest failed: {r.status_code}"
    ctx = r.json()
    print(f"  Context: {ctx['title']}")
    return ctx


def main():
    errors = []
    ctx = get_context()

    # 1. Podcast endpoint
    print("\n=== Testing /api/podcast ===")
    try:
        r = httpx.post(
            f"{BASE}/api/podcast",
            json=ctx,
            timeout=300,  # TTS can take a while
        )
        assert r.status_code == 200, f"Status {r.status_code}: {r.text[:200]}"
        podcast = r.json()

        # Check script
        assert "script" in podcast, "Missing 'script'"
        script = podcast["script"]
        assert isinstance(script, list), f"Script is not a list: {type(script)}"
        assert len(script) >= 20, f"Only {len(script)} dialogue turns (need >=20)"

        # Check speakers
        speakers = set(line.get("speaker") for line in script)
        assert "A" in speakers or "Alex" in speakers, f"Missing speaker A/Alex: {speakers}"
        assert "B" in speakers or "Sam" in speakers, f"Missing speaker B/Sam: {speakers}"

        # Check segments
        segments = set(line.get("segment", 0) for line in script)
        assert len(segments) >= 3, f"Only {len(segments)} segments (need >=3)"

        print(f"  Dialogue turns: {len(script)}")
        print(f"  Speakers: {speakers}")
        print(f"  Segments: {sorted(segments)}")

        # Check audio URL
        assert "audio_url" in podcast, "Missing 'audio_url'"
        audio_url = podcast["audio_url"]
        print(f"  Audio URL: {audio_url}")

        # Check audio file exists and has content
        audio_path = audio_url.replace("/static/", "/tmp/digest/")
        if os.path.exists(audio_path):
            size = os.path.getsize(audio_path)
            size_kb = size // 1024
            assert size > 100_000, f"Audio file too small: {size_kb}KB (need >100KB)"
            print(f"  Audio file: {size_kb}KB")
        else:
            print(f"  Audio file not found at {audio_path} (may be served differently)")

        # Preview script
        for line in script[:4]:
            speaker = line.get("speaker", "?")
            text = line.get("text", "")[:80]
            print(f"    [{speaker}] {text}...")

        print("  /api/podcast PASSED")
    except Exception as e:
        errors.append(f"/api/podcast: {e}")
        print(f"  /api/podcast FAILED: {e}")

    # Summary
    print(f"\n{'='*50}")
    if errors:
        print(f"Round 4 FAILED ({len(errors)} errors):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("Round 4 PASSED")


if __name__ == "__main__":
    main()
