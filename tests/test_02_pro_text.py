"""Test 2: Gemini 3.1 Pro — longer generation + system instructions."""
import os, json
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# Pro with system instruction — podcast script style
print("=== Gemini 3.1 Pro: System Instruction + Long Gen ===")
r = client.models.generate_content(
    model="gemini-3.1-pro-preview",
    contents="Write a short 4-turn podcast dialogue between Alex and Sam about why spaced repetition works for learning.",
    config=types.GenerateContentConfig(
        system_instruction="You are a podcast scriptwriter. Output JSON array of {speaker, text} objects. No markdown.",
        response_mime_type="application/json",
        temperature=1.0,
            thinking_config=types.ThinkingConfig(thinking_level="LOW"),
        max_output_tokens=2000,
    ),
)
script = json.loads(r.text)
print(json.dumps(script[:2], indent=2, ensure_ascii=False))
print(f"... ({len(script)} turns total)")
assert len(script) >= 4, f"Expected >= 4 turns, got {len(script)}"

print("\nTest 2 PASSED")
