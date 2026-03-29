"""Test 9: Full pipeline simulation — ingest URL, analyze, generate quiz + cards."""
import os, json
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

OUT_DIR = os.path.join(os.path.dirname(__file__), "samples")
os.makedirs(OUT_DIR, exist_ok=True)

# Use saved web content or inline text
web_content_path = os.path.join(OUT_DIR, "web_content.txt")
if os.path.exists(web_content_path):
    with open(web_content_path) as f:
        source_text = f.read()
    print(f"Using saved web content ({len(source_text)} chars)")
else:
    source_text = """
    Harness design for long-running application development. The piece explores
    how to improve Claude's performance on frontend design and autonomous app building.
    Key concepts: multi-agent architecture, generator-evaluator pattern, context management,
    compaction vs context resets, design quality criteria.
    """
    print("Using inline fallback text")

# Step 1: Context analysis (like ingest.py)
print("\n=== Step 1: Context Analysis (Flash) ===")
analysis_prompt = """Analyze the provided content and extract a structured learning context.
OUTPUT: JSON only. No markdown.
{
  "title": "Clear title (5-10 words)",
  "summary": "3 sentences.",
  "key_concepts": [{"term": "Name", "definition": "One sentence."}],
  "key_insights": ["insight1", "insight2", "insight3"]
}"""

r = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=[source_text[:6000], analysis_prompt],
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=1.0,
            thinking_config=types.ThinkingConfig(thinking_level="LOW"),
    ),
)
context = json.loads(r.text)
print(f"Title: {context['title']}")
print(f"Concepts: {len(context.get('key_concepts', []))}")
print(f"Insights: {len(context.get('key_insights', []))}")
assert "title" in context
assert len(context.get("key_concepts", [])) >= 3

# Step 2: Quiz generation
print("\n=== Step 2: Quiz Generation (Flash) ===")
r2 = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=[
        json.dumps(context),
        'Generate 5 multiple-choice questions. Output JSON: {"questions": [{"question":"...", "options":["A)...","B)...","C)...","D)..."], "correct":0, "explanation":"..."}]}',
    ],
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=1.0,
            thinking_config=types.ThinkingConfig(thinking_level="LOW"),
    ),
)
quiz = json.loads(r2.text)
print(f"Questions: {len(quiz['questions'])}")
for q in quiz["questions"][:2]:
    print(f"  Q: {q['question'][:80]}...")
assert len(quiz["questions"]) >= 3

# Step 3: Flashcards
print("\n=== Step 3: Flashcard Generation (Flash) ===")
r3 = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=[
        json.dumps(context),
        'Generate 8 flashcards. Output JSON: {"cards": [{"front":"...", "back":"...", "type":"definition|comparison|application"}]}',
    ],
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=1.0,
            thinking_config=types.ThinkingConfig(thinking_level="LOW"),
    ),
)
cards = json.loads(r3.text)
print(f"Cards: {len(cards['cards'])}")
for c in cards["cards"][:2]:
    print(f"  [{c.get('type','?')}] {c['front']}")
assert len(cards["cards"]) >= 5

# Save all outputs
with open(os.path.join(OUT_DIR, "pipeline_context.json"), "w") as f:
    json.dump(context, f, indent=2, ensure_ascii=False)
with open(os.path.join(OUT_DIR, "pipeline_quiz.json"), "w") as f:
    json.dump(quiz, f, indent=2, ensure_ascii=False)
with open(os.path.join(OUT_DIR, "pipeline_cards.json"), "w") as f:
    json.dump(cards, f, indent=2, ensure_ascii=False)

print("\nTest 9 PASSED (all outputs saved to tests/samples/)")
