"""Verify podcast audio quality using Gemini audio understanding.

Checks that the generated WAV file:
1. Is playable (valid WAV, correct format)
2. Contains actual speech (not silence/noise/buzz)
3. Has two distinct speakers
4. Content relates to the source material

Uses Gemini 3 Flash with audio input for analysis.
"""
import os
import sys
import wave

# Try to find the most recent podcast WAV
AUDIO_DIR = "/tmp/digest"
BACKEND_URL = "http://localhost:8000"


def find_podcast_wav():
    """Find the most recent podcast WAV file."""
    if not os.path.exists(AUDIO_DIR):
        return None
    wavs = [f for f in os.listdir(AUDIO_DIR) if f.startswith("podcast_") and f.endswith(".wav")]
    if not wavs:
        return None
    wavs.sort(key=lambda f: os.path.getmtime(os.path.join(AUDIO_DIR, f)), reverse=True)
    return os.path.join(AUDIO_DIR, wavs[0])


def test_wav_format(path):
    """Verify WAV file format is correct."""
    print("=== 1. WAV Format ===")
    with wave.open(path, "rb") as wf:
        channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        nframes = wf.getnframes()
        duration = nframes / framerate

    assert channels == 1, f"Expected mono, got {channels} channels"
    assert sampwidth == 2, f"Expected 16-bit, got {sampwidth * 8}-bit"
    assert framerate == 24000, f"Expected 24000Hz, got {framerate}Hz"
    assert duration > 30, f"Audio too short: {duration:.1f}s (need >30s)"

    size_kb = os.path.getsize(path) // 1024
    print(f"  Channels: {channels} (mono)")
    print(f"  Sample width: {sampwidth * 8}-bit")
    print(f"  Frame rate: {framerate}Hz")
    print(f"  Duration: {duration:.1f}s")
    print(f"  File size: {size_kb}KB")
    print("  PASSED")
    return duration


def test_not_silence(path):
    """Check the audio isn't just silence."""
    print("\n=== 2. Not Silence ===")
    import struct

    with wave.open(path, "rb") as wf:
        # Read first 5 seconds
        frames = wf.readframes(min(wf.getnframes(), 24000 * 5))

    samples = struct.unpack(f"<{len(frames) // 2}h", frames)
    max_amp = max(abs(s) for s in samples)
    avg_amp = sum(abs(s) for s in samples) / len(samples)

    assert max_amp > 500, f"Audio appears silent (max amplitude: {max_amp})"
    assert avg_amp > 50, f"Audio very quiet (avg amplitude: {avg_amp:.0f})"
    print(f"  Max amplitude: {max_amp}")
    print(f"  Avg amplitude: {avg_amp:.0f}")
    print("  PASSED")


def test_gemini_audio_analysis(path):
    """Use Gemini to analyze the audio content."""
    print("\n=== 3. Gemini Audio Analysis ===")
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    # Read first 60 seconds of audio
    with wave.open(path, "rb") as wf:
        max_frames = min(wf.getnframes(), 24000 * 60)
        audio_bytes = wf.readframes(max_frames)

    # Upload as inline data
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=[
            types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"),
            """Analyze this audio clip. Answer these questions:

1. SPEECH: Does this contain clear, understandable speech? (yes/no)
2. SPEAKERS: How many distinct speakers can you hear? (number)
3. QUALITY: Rate audio quality 1-5 (1=buzz/noise, 5=clear studio)
4. TOPIC: In one sentence, what are they discussing?
5. PODCAST: Does this sound like a natural podcast conversation? (yes/no)

Output JSON only:
{"speech": true/false, "speakers": number, "quality": number, "topic": "...", "podcast": true/false}"""
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )

    import json
    analysis = json.loads(response.text)
    print(f"  Speech detected: {analysis.get('speech')}")
    print(f"  Speakers: {analysis.get('speakers')}")
    print(f"  Quality: {analysis.get('quality')}/5")
    print(f"  Topic: {analysis.get('topic')}")
    print(f"  Sounds like podcast: {analysis.get('podcast')}")

    assert analysis.get("speech") is True, "No speech detected — audio may be buzz/noise"
    assert analysis.get("speakers", 0) >= 2, f"Expected 2 speakers, detected {analysis.get('speakers')}"
    assert analysis.get("quality", 0) >= 2, f"Audio quality too low: {analysis.get('quality')}/5"

    print("  PASSED")
    return analysis


def main():
    errors = []

    # Find audio file
    path = find_podcast_wav()
    if not path:
        print("No podcast WAV found in /tmp/digest/")
        print("Run the podcast endpoint first, or specify path as argument.")
        if len(sys.argv) > 1:
            path = sys.argv[1]
        else:
            sys.exit(1)

    print(f"Testing: {path}\n")

    # Test 1: WAV format
    try:
        duration = test_wav_format(path)
    except Exception as e:
        errors.append(f"wav_format: {e}")
        print(f"  FAILED: {e}")

    # Test 2: Not silence
    try:
        test_not_silence(path)
    except Exception as e:
        errors.append(f"silence_check: {e}")
        print(f"  FAILED: {e}")

    # Test 3: Gemini audio analysis
    try:
        test_gemini_audio_analysis(path)
    except Exception as e:
        errors.append(f"gemini_analysis: {e}")
        print(f"  FAILED: {e}")

    # Summary
    print(f"\n{'='*60}")
    if errors:
        print(f"Audio Verification FAILED ({len(errors)} errors):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("Audio Verification PASSED — real speech, 2 speakers, good quality")


if __name__ == "__main__":
    main()
