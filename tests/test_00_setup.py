"""Test 0: Verify setup — API key, SDK import, list models."""
import os
from google import genai

API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
assert API_KEY, "No GEMINI_API_KEY or GOOGLE_API_KEY set"

client = genai.Client(api_key=API_KEY)

# List available models
print("=== Available Models ===")
for m in client.models.list():
    name = m.name
    if any(k in name for k in ["flash", "pro", "tts", "live"]):
        print(f"  {name}")

print("\nSetup OK")
