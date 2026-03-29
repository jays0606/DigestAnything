"""Podcast — context → script → parallel TTS → merged WAV."""
import asyncio
import json
import os
import wave
from collections import defaultdict

from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

PODCAST_PROMPT = """Write a podcast script for two hosts.

HOSTS:
- Alex (A): Smart beginner. Asks great questions. Uses analogies.
  Sometimes gets things slightly wrong so Sam can correct.
  Says "wait hold on", "oh so it's like..."
- Sam (B): Expert who simplifies. Enthusiastic.
  Says "exactly!", "here's the key thing", "this is where it gets interesting"

STRUCTURE — 6 SEGMENTS:
Segment 1 HOOK (~30s): Surprising fact or bold claim. NO "welcome to our podcast".
Segment 2 FOUNDATION (~2min): Core problem/context.
Segment 3 CORE INSIGHT (~2min): Main idea step by step. At least one analogy.
Segment 4 DEEP DIVE (~2min): Technical details. Edge cases.
Segment 5 IMPLICATIONS (~1min): Real world impact.
Segment 6 CLOSING (~30s): Surprising insight or thought-provoking question. NOT a summary.

RULES:
- Include filler: "oh!", "right right", "that's wild", "hmm"
- At least 3 moments of laughter or surprise
- Reference specific details from source
- Total ~1000-1200 words
- Generate 30-40 dialogue turns total. Do NOT exceed 40 turns."""

PODCAST_SCHEMA = {
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


async def generate_script(context: dict) -> list[dict]:
    """Generate podcast script from context."""
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=[json.dumps(context), PODCAST_PROMPT],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=PODCAST_SCHEMA,
            temperature=1.0,
            thinking_config=types.ThinkingConfig(thinking_level="LOW"),
        ),
    )
    return json.loads(response.text)


async def tts_segment(segment_num: int, lines: list[dict]) -> bytes:
    """Generate TTS audio for one segment."""
    tts_input = ""
    for line in lines:
        speaker = "Alex" if line["speaker"] == "A" else "Sam"
        tts_input += f"\n{speaker}: {line['text']}"

    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=tts_input.strip(),
        config=TTS_CONFIG,
    )
    return response.candidates[0].content.parts[0].inline_data.data


async def generate_podcast(context: dict, session_id: str) -> dict:
    """Full podcast pipeline: script → parallel TTS → merged WAV."""
    # Step 1: Generate script
    script = await generate_script(context)

    # Step 2: Group by segment
    segments: dict[int, list[dict]] = defaultdict(list)
    for line in script:
        segments[line["segment"]].append(line)

    # Step 3: Parallel TTS for all segments
    segment_nums = sorted(segments.keys())
    tts_tasks = [tts_segment(num, segments[num]) for num in segment_nums]
    audio_chunks = await asyncio.gather(*tts_tasks)

    # Step 4: Merge PCM → WAV
    os.makedirs("/tmp/digest", exist_ok=True)
    wav_path = f"/tmp/digest/podcast_{session_id}.wav"
    merged_pcm = b"".join(audio_chunks)

    with wave.open(wav_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(merged_pcm)

    audio_url = f"/static/podcast_{session_id}.wav"

    return {
        "script": script,
        "audio_url": audio_url,
    }
