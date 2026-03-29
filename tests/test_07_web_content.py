"""Test 7: Web content extraction with trafilatura + Gemini analysis."""
import os, json
import trafilatura
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

URL = "https://www.anthropic.com/engineering/harness-design-long-running-apps"

print(f"=== Web Content: {URL} ===")

# Extract text
print("Fetching & extracting...")
html = trafilatura.fetch_url(URL)
assert html, "Failed to fetch URL"
text = trafilatura.extract(html)
assert text and len(text) > 200, f"Extraction too short: {len(text) if text else 0} chars"
print(f"Extracted {len(text)} chars")
print(f"First 200: {text[:200]}...\n")

# Analyze with Gemini
print("Analyzing with Gemini 3 Flash...")
r = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=[
        text[:8000],  # trim to avoid token limits
        "Extract 5 key concepts from this article. Output JSON: {\"concepts\": [{\"term\": \"...\", \"definition\": \"...\"}]}",
    ],
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=1.0,
            thinking_config=types.ThinkingConfig(thinking_level="LOW"),
    ),
)
data = json.loads(r.text)
print(json.dumps(data, indent=2))
assert "concepts" in data
assert len(data["concepts"]) >= 3

# Save
OUT_DIR = os.path.join(os.path.dirname(__file__), "samples")
os.makedirs(OUT_DIR, exist_ok=True)
with open(os.path.join(OUT_DIR, "web_content.txt"), "w") as f:
    f.write(text[:5000])

print("\nTest 7 PASSED")
