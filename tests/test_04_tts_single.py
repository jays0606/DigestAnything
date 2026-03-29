"""Test 4: Gemini 2.5 Flash TTS — single speaker."""
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


print("=== TTS Single Speaker (Kore voice) ===")
r = client.models.generate_content(
    model="gemini-2.5-flash-preview-tts",
    contents="Say cheerfully: Welcome to Digest! Let's turn any source into a learning experience.",
    config=types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")
            )
        ),
    ),
)

audio_data = r.candidates[0].content.parts[0].inline_data.data
out_path = os.path.join(OUT_DIR, "tts_single.wav")
save_wav(out_path, audio_data)
size_kb = os.path.getsize(out_path) // 1024
print(f"Saved: {out_path} ({size_kb}KB)")
assert size_kb > 5, "Audio file too small"

print("\nTest 4 PASSED")
