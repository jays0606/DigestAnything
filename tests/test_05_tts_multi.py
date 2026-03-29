"""Test 5: Gemini 2.5 Flash TTS — multi-speaker podcast style."""
import os, wave
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

OUT_DIR = os.path.join(os.path.dirname(__file__), "samples")
os.makedirs(OUT_DIR, exist_ok=True)


def save_wav(filename, pcm_data, channels=1, rate=24000, sample_width=2):
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm_data)


print("=== TTS Multi-Speaker (Podcast Style) ===")

script = """
Turn [Alex]: Oh wait, so you're telling me that spaced repetition actually changes how your brain stores memories?
Turn [Sam]: Exactly! Here's the key thing — when you review at increasing intervals, you're strengthening the neural pathways right before they would decay.
Turn [Alex]: That's wild. So it's like... exercising a muscle right before it atrophies?
Turn [Sam]: That's a great analogy! And the best part is, each time you successfully recall something, the interval gets longer.
"""

config = types.GenerateContentConfig(
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

r = client.models.generate_content(
    model="gemini-2.5-flash-preview-tts",
    contents=script,
    config=config,
)

audio_data = r.candidates[0].content.parts[0].inline_data.data
out_path = os.path.join(OUT_DIR, "tts_multi.wav")
save_wav(out_path, audio_data)
size_kb = os.path.getsize(out_path) // 1024
print(f"Saved: {out_path} ({size_kb}KB)")
assert size_kb > 10, "Audio file too small for multi-speaker"

print("\nTest 5 PASSED")
