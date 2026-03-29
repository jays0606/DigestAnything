"""Test 11: TTS chunked podcast — generate audio per segment in parallel, then merge.
Simulates the real podcast pipeline: script → chunk by segment → TTS per chunk → concat WAV.
"""
import os, json, wave, time, concurrent.futures
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-3-flash-preview"
TTS_MODEL = "gemini-2.5-flash-preview-tts"

OUT_DIR = os.path.join(os.path.dirname(__file__), "samples")
os.makedirs(OUT_DIR, exist_ok=True)


def save_wav(filename, pcm_data, channels=1, rate=24000, sample_width=2):
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm_data)


TTS_CONFIG = types.GenerateContentConfig(
    response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(
        multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
            speaker_voice_configs=[
                types.SpeakerVoiceConfig(
                    speaker="Alex",
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")
                    ),
                ),
                types.SpeakerVoiceConfig(
                    speaker="Sam",
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")
                    ),
                ),
            ]
        )
    ),
)

# ============================================================
# Step 1: Load or generate a short podcast script (3 segments)
# ============================================================
print("=" * 60)
print("Step 1: Generate short podcast script (3 segments, ~3 min)")
print("=" * 60)

# Use a shorter script for testing TTS limits (3 segments instead of 6)
SCRIPT_PROMPT = """Write a 3-minute podcast dialogue between Alex and Sam about why spaced repetition works.

HOSTS:
- Alex (A): Curious beginner, asks questions
- Sam (B): Expert who simplifies

STRUCTURE — 3 SEGMENTS:
Segment 1 HOOK: Bold claim to grab attention. 3-4 turns.
Segment 2 CORE: Explain spaced repetition step by step. 8-10 turns.
Segment 3 CLOSING: Practical takeaway. 3-4 turns.

RULES:
- Natural dialogue with filler ("oh!", "right", "hmm")
- Generate 15-20 turns total
- Each turn should be 1-3 sentences"""

podcast_schema = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "speaker": {"type": "STRING", "enum": ["A", "B"]},
            "text": {"type": "STRING"},
            "segment": {"type": "INTEGER"},
        },
        "required": ["speaker", "text", "segment"],
    },
}

t0 = time.time()
r = client.models.generate_content(
    model=MODEL,
    contents=SCRIPT_PROMPT,
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=podcast_schema,
        temperature=1.0,
        thinking_config=types.ThinkingConfig(thinking_level="LOW"),
    ),
)
script = json.loads(r.text)
print(f"  Turns: {len(script)}")
print(f"  Segments: {sorted(set(t['segment'] for t in script))}")
total_words = sum(len(t["text"].split()) for t in script)
print(f"  Total words: {total_words}")
print(f"  Time: {time.time() - t0:.1f}s")

# ============================================================
# Step 2: Chunk by segment → build TTS input per chunk
# ============================================================
print("\n" + "=" * 60)
print("Step 2: Chunk by segment → TTS input")
print("=" * 60)

segments = {}
for line in script:
    seg = line.get("segment", 1)
    segments.setdefault(seg, []).append(line)

tts_inputs = {}
for seg_num in sorted(segments.keys()):
    tts_text = ""
    for line in segments[seg_num]:
        speaker = "Alex" if line["speaker"] == "A" else "Sam"
        tts_text += f"\n{speaker}: {line['text']}"
    tts_inputs[seg_num] = tts_text.strip()
    word_count = len(tts_text.split())
    print(f"  Segment {seg_num}: {len(segments[seg_num])} turns, {word_count} words")

# ============================================================
# Step 3: Generate TTS per segment (sequential — parallel would need async)
# ============================================================
print("\n" + "=" * 60)
print("Step 3: TTS per segment")
print("=" * 60)

audio_chunks = {}
total_tts_time = 0

for seg_num in sorted(tts_inputs.keys()):
    print(f"  Segment {seg_num}...", end=" ", flush=True)
    t0 = time.time()
    try:
        r = client.models.generate_content(
            model=TTS_MODEL,
            contents=tts_inputs[seg_num],
            config=TTS_CONFIG,
        )
        audio_data = r.candidates[0].content.parts[0].inline_data.data
        dt = time.time() - t0
        total_tts_time += dt
        audio_chunks[seg_num] = audio_data
        size_kb = len(audio_data) // 1024
        duration_est = len(audio_data) / (24000 * 2)  # PCM 24kHz 16-bit mono
        print(f"OK ({size_kb}KB, ~{duration_est:.0f}s audio, took {dt:.1f}s)")

        # Save individual segment
        seg_path = os.path.join(OUT_DIR, f"podcast_seg{seg_num}.wav")
        save_wav(seg_path, audio_data)
    except Exception as e:
        dt = time.time() - t0
        print(f"FAILED ({dt:.1f}s): {e}")
        audio_chunks[seg_num] = None

print(f"\n  Total TTS time: {total_tts_time:.1f}s")

# ============================================================
# Step 4: Merge all segments into one WAV
# ============================================================
print("\n" + "=" * 60)
print("Step 4: Merge segments")
print("=" * 60)

successful = [audio_chunks[k] for k in sorted(audio_chunks.keys()) if audio_chunks[k]]
if not successful:
    print("  No audio segments generated!")
    exit(1)

merged_pcm = b"".join(successful)
merged_path = os.path.join(OUT_DIR, "podcast_merged.wav")
save_wav(merged_path, merged_pcm)

merged_size_kb = os.path.getsize(merged_path) // 1024
merged_duration = len(merged_pcm) / (24000 * 2)

print(f"  Segments merged: {len(successful)}/{len(audio_chunks)}")
print(f"  Merged file: {merged_path}")
print(f"  Size: {merged_size_kb}KB")
print(f"  Estimated duration: {merged_duration:.0f}s ({merged_duration/60:.1f}min)")

assert merged_size_kb > 100, "Merged audio too small"
assert len(successful) >= 2, "Too few segments generated"

print(f"\nTest 11 PASSED")
print(f"  Script: {len(script)} turns, {total_words} words")
print(f"  Audio: {merged_duration:.0f}s across {len(successful)} segments")
print(f"  Total TTS time: {total_tts_time:.1f}s")
