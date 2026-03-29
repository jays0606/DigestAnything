"""Test 1: Gemini 3 Flash — basic text generation."""
import os, json
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# Basic text
print("=== Gemini 3 Flash: Basic Text ===")
r = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="Explain context windows in LLMs in 2 sentences.",
)
print(r.text)
assert len(r.text) > 20, "Response too short"

# Structured JSON output
print("\n=== Gemini 3 Flash: JSON Output ===")
r2 = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="List 3 popular programming languages with their main use case.",
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema={
            "type": "OBJECT",
            "properties": {
                "languages": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "name": {"type": "STRING"},
                            "use_case": {"type": "STRING"},
                        },
                    },
                }
            },
        },
        temperature=1.0,
            thinking_config=types.ThinkingConfig(thinking_level="LOW"),
    ),
)
data = json.loads(r2.text)
print(json.dumps(data, indent=2))
assert "languages" in data
assert len(data["languages"]) >= 3

# Streaming
print("\n=== Gemini 3 Flash: Streaming ===")
chunks = 0
for chunk in client.models.generate_content_stream(
    model="gemini-3-flash-preview",
    contents="Write a haiku about AI.",
):
    print(chunk.text, end="")
    chunks += 1
print(f"\n(streamed in {chunks} chunks)")
assert chunks >= 1

print("\nTest 1 PASSED")
