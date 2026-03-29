"""Test 8: Video understanding — download a short clip and analyze with Gemini."""
import os, subprocess, time
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

OUT_DIR = os.path.join(os.path.dirname(__file__), "samples")
os.makedirs(OUT_DIR, exist_ok=True)
VIDEO_PATH = os.path.join(OUT_DIR, "sample_video.mp4")

# Download a short sample video (Big Buck Bunny, 10s clip, public domain)
if not os.path.exists(VIDEO_PATH):
    print("Downloading short sample video...")
    subprocess.run(
        [
            "curl",
            "-L",
            "-o",
            VIDEO_PATH,
            "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/Big_Buck_Bunny_360_10s_1MB.mp4",
        ],
        check=True,
        capture_output=True,
    )

size_kb = os.path.getsize(VIDEO_PATH) // 1024
print(f"=== Video Understanding: {VIDEO_PATH} ({size_kb}KB) ===")

# Upload
print("Uploading to Gemini Files API...")
uploaded = client.files.upload(file=VIDEO_PATH)
print(f"Uploaded: {uploaded.name}")

# Wait for processing
print("Waiting for processing...")
for _ in range(30):
    f = client.files.get(name=uploaded.name)
    if f.state.name == "ACTIVE":
        break
    time.sleep(2)
else:
    print("WARNING: File still processing after 60s")

# Analyze
print("Analyzing video with Gemini 3 Flash...")
r = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=[
        types.Part.from_uri(file_uri=uploaded.uri, mime_type="video/mp4"),
        "Describe what happens in this video in 2-3 sentences.",
    ],
)
print(f"Response: {r.text}")
assert len(r.text) > 20, "Video analysis too short"

# Cleanup
client.files.delete(name=uploaded.name)
print("File deleted.")

print("\nTest 8 PASSED")
