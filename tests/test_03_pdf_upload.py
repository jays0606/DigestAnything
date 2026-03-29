"""Test 3: PDF upload via Files API + analysis."""
import os, json
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

PDF_PATH = os.path.join(os.path.dirname(__file__), "..", "Eric-Jorgenson_The-Almanack-of-Naval-Ravikant_Final.pdf")
PDF_PATH = os.path.abspath(PDF_PATH)

assert os.path.exists(PDF_PATH), f"PDF not found: {PDF_PATH}"
print(f"=== PDF Upload: {os.path.basename(PDF_PATH)} ({os.path.getsize(PDF_PATH) // 1024}KB) ===")

# Upload
print("Uploading...")
uploaded = client.files.upload(file=PDF_PATH)
print(f"Uploaded: {uploaded.name} ({uploaded.uri})")

# Analyze with Flash
print("\nAnalyzing with Gemini 3 Flash...")
r = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=[
        types.Part.from_uri(file_uri=uploaded.uri, mime_type="application/pdf"),
        "Summarize this book in 3 bullet points. What are the key themes?",
    ],
)
print(r.text)
assert len(r.text) > 50

# Cleanup
client.files.delete(name=uploaded.name)
print("File deleted.")

print("\nTest 3 PASSED")
