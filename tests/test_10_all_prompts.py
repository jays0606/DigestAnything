"""Test 10: Audit every prompt — exact JSON schemas, proper response_schema enforcement.
Tests each pipeline stage with the real prompts from SPEC.md against Gemini 3 Flash.
"""
import os, json, time
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-3-flash-preview"

OUT_DIR = os.path.join(os.path.dirname(__file__), "samples")
os.makedirs(OUT_DIR, exist_ok=True)

# Load saved web content as source
web_path = os.path.join(OUT_DIR, "web_content.txt")
if os.path.exists(web_path):
    with open(web_path) as f:
        SOURCE_TEXT = f.read()
else:
    SOURCE_TEXT = "Harness design for long-running application development explores multi-agent architectures, context resets, generator-evaluator patterns, and design quality criteria for autonomous coding."

COMMON_CONFIG = dict(
    temperature=1.0,
    thinking_config=types.ThinkingConfig(thinking_level="LOW"),
)

# ============================================================
# PROMPT 1: Source Analysis
# ============================================================
print("=" * 60)
print("PROMPT 1: Source Analysis")
print("=" * 60)

ANALYSIS_PROMPT = """You are a world-class learning content designer.

Analyze the provided content and extract a structured learning context.

RULES:
- Generate exactly 10-15 key_concepts
- Generate exactly 3-5 hierarchy children with 2-4 children each
- Generate exactly 3-5 key_insights
- Generate exactly 2-4 analogies
- Definitions understandable by a smart 16-year-old
- Hierarchy labels SHORT (3-5 words) — they render as mindmap nodes
- Insights should make someone say "oh interesting"
"""

analysis_schema = {
    "type": "OBJECT",
    "properties": {
        "title": {"type": "STRING", "description": "Clear title, 5-10 words"},
        "subtitle": {"type": "STRING", "description": "One-line description"},
        "summary": {"type": "STRING", "description": "3 sentences. What it is. Key insight. Why it matters."},
        "difficulty": {"type": "STRING", "enum": ["beginner", "intermediate", "advanced"]},
        "estimated_read_time_minutes": {"type": "INTEGER"},
        "key_concepts": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "term": {"type": "STRING"},
                    "definition": {"type": "STRING", "description": "One clear sentence."},
                    "importance": {"type": "STRING", "enum": ["high", "medium"]},
                    "related_to": {"type": "ARRAY", "items": {"type": "STRING"}},
                },
                "required": ["term", "definition", "importance"],
            },
        },
        "hierarchy": {
            "type": "OBJECT",
            "properties": {
                "root": {"type": "STRING", "description": "Main topic, 3-4 words"},
                "children": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "name": {"type": "STRING", "description": "Subtopic, 3-4 words"},
                            "children": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "description": {"type": "STRING"},
                        },
                        "required": ["name", "children"],
                    },
                },
            },
            "required": ["root", "children"],
        },
        "key_insights": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
        },
        "analogies": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "concept": {"type": "STRING"},
                    "analogy": {"type": "STRING"},
                    "explanation": {"type": "STRING"},
                },
                "required": ["concept", "analogy", "explanation"],
            },
        },
    },
    "required": ["title", "subtitle", "summary", "difficulty", "key_concepts", "hierarchy", "key_insights", "analogies"],
}

t0 = time.time()
r = client.models.generate_content(
    model=MODEL,
    contents=[SOURCE_TEXT[:8000], ANALYSIS_PROMPT],
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=analysis_schema,
        **COMMON_CONFIG,
    ),
)
context = json.loads(r.text)
dt = time.time() - t0

print(f"  Title: {context['title']}")
print(f"  Subtitle: {context['subtitle']}")
print(f"  Difficulty: {context['difficulty']}")
print(f"  Concepts: {len(context['key_concepts'])}")
print(f"  Hierarchy root: {context['hierarchy']['root']}")
print(f"  Hierarchy children: {len(context['hierarchy']['children'])}")
print(f"  Insights: {len(context['key_insights'])}")
print(f"  Analogies: {len(context['analogies'])}")
print(f"  Time: {dt:.1f}s")

assert len(context["key_concepts"]) >= 4, f"Too few concepts: {len(context['key_concepts'])}"
assert len(context["hierarchy"]["children"]) >= 3, f"Too few hierarchy children"
assert len(context["key_insights"]) >= 3, f"Too few insights"
assert len(context["analogies"]) >= 2, f"Too few analogies"
assert context["difficulty"] in ["beginner", "intermediate", "advanced"]
for c in context["key_concepts"]:
    assert c["importance"] in ["high", "medium"], f"Bad importance: {c['importance']}"
print("  PASSED\n")

# Save for downstream tests
with open(os.path.join(OUT_DIR, "prompt_context.json"), "w") as f:
    json.dump(context, f, indent=2, ensure_ascii=False)

# ============================================================
# PROMPT 2: Markmap
# ============================================================
print("=" * 60)
print("PROMPT 2: Markmap Diagram")
print("=" * 60)

MARKMAP_PROMPT = """Convert this hierarchy into a markdown outline for a mindmap.

RULES:
- # for main topic
- ## for major branches (3-5 max)
- ### for sub-concepts
- Bullet points (-) for 1-sentence leaf details
- Keep labels under 5 words
- Use emoji prefixes for key nodes
- Max 3 heading levels, 10-15 nodes total

INPUT: {hierarchy}

OUTPUT: Markdown only. No backticks. Start with #."""

t0 = time.time()
r = client.models.generate_content(
    model=MODEL,
    contents=MARKMAP_PROMPT.format(hierarchy=json.dumps(context["hierarchy"])),
    config=types.GenerateContentConfig(
        **COMMON_CONFIG,
    ),
)
markmap_md = r.text.strip()
dt = time.time() - t0

lines = markmap_md.split("\n")
h1_count = sum(1 for l in lines if l.startswith("# ") and not l.startswith("## "))
h2_count = sum(1 for l in lines if l.startswith("## ") and not l.startswith("### "))
h3_count = sum(1 for l in lines if l.startswith("### "))

print(f"  Lines: {len(lines)}")
print(f"  H1: {h1_count}, H2: {h2_count}, H3: {h3_count}")
print(f"  First 3 lines: {lines[:3]}")
print(f"  Time: {dt:.1f}s")

assert h1_count >= 1, "Missing # heading"
assert h2_count >= 3, f"Too few ## branches: {h2_count}"
assert len(lines) >= 8, f"Too few lines: {len(lines)}"
print("  PASSED\n")

# ============================================================
# PROMPT 3: Quiz
# ============================================================
print("=" * 60)
print("PROMPT 3: Quiz (10 MCQs)")
print("=" * 60)

QUIZ_PROMPT = """Generate 10 multiple-choice questions testing deep understanding.

DIFFICULTY:
- Q1-3: Easy (recall, basic definitions)
- Q4-7: Medium (application, "what would happen if...")
- Q8-9: Hard (synthesis, edge cases)
- Q10: Expert (connect multiple concepts)

PER QUESTION:
- 4 options (A, B, C, D)
- Wrong answers must be plausible (common misconceptions)
- "correct": index 0-3
- "explanation": 2-3 sentences
- At least 2 scenario questions
- At least 1 relationship question
- Test UNDERSTANDING not memorization"""

quiz_schema = {
    "type": "OBJECT",
    "properties": {
        "questions": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "INTEGER"},
                    "difficulty": {"type": "STRING", "enum": ["easy", "medium", "hard", "expert"]},
                    "question": {"type": "STRING"},
                    "options": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "correct": {"type": "INTEGER", "description": "Index 0-3"},
                    "explanation": {"type": "STRING"},
                },
                "required": ["id", "difficulty", "question", "options", "correct", "explanation"],
            },
        },
    },
    "required": ["questions"],
}

t0 = time.time()
r = client.models.generate_content(
    model=MODEL,
    contents=[json.dumps(context), QUIZ_PROMPT],
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=quiz_schema,
        **COMMON_CONFIG,
    ),
)
quiz = json.loads(r.text)
dt = time.time() - t0

print(f"  Questions: {len(quiz['questions'])}")
difficulties = [q["difficulty"] for q in quiz["questions"]]
print(f"  Difficulties: {difficulties}")
for q in quiz["questions"]:
    assert len(q["options"]) == 4, f"Q{q['id']} has {len(q['options'])} options, expected 4"
    assert 0 <= q["correct"] <= 3, f"Q{q['id']} correct={q['correct']} out of range"
    assert q["difficulty"] in ["easy", "medium", "hard", "expert"]
    assert len(q["explanation"]) > 20, f"Q{q['id']} explanation too short"
print(f"  Sample: {quiz['questions'][0]['question'][:80]}...")
print(f"  Time: {dt:.1f}s")

assert len(quiz["questions"]) >= 8, f"Too few questions: {len(quiz['questions'])}"
print("  PASSED\n")

# ============================================================
# PROMPT 4: Flashcards
# ============================================================
print("=" * 60)
print("PROMPT 4: Flashcards (12-15)")
print("=" * 60)

CARDS_PROMPT = """Generate 12-15 flashcards for spaced repetition.

CARD TYPES (mix):
- Definition (6-8): Term → definition + example
- Comparison (2-3): "X vs Y" → key differences
- Application (2-3): Scenario → correct approach

RULES:
- Front: 1-6 words max
- Back: 2-3 sentences max. Self-contained.
- Order: foundational → advanced"""

cards_schema = {
    "type": "OBJECT",
    "properties": {
        "cards": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "front": {"type": "STRING", "description": "1-6 words"},
                    "back": {"type": "STRING", "description": "2-3 sentences"},
                    "type": {"type": "STRING", "enum": ["definition", "comparison", "application"]},
                },
                "required": ["front", "back", "type"],
            },
        },
    },
    "required": ["cards"],
}

t0 = time.time()
r = client.models.generate_content(
    model=MODEL,
    contents=[json.dumps(context), CARDS_PROMPT],
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=cards_schema,
        **COMMON_CONFIG,
    ),
)
cards = json.loads(r.text)
dt = time.time() - t0

card_types = [c["type"] for c in cards["cards"]]
print(f"  Cards: {len(cards['cards'])}")
print(f"  Types: definition={card_types.count('definition')}, comparison={card_types.count('comparison')}, application={card_types.count('application')}")
for c in cards["cards"]:
    assert c["type"] in ["definition", "comparison", "application"]
    front_words = len(c["front"].split())
    assert front_words <= 10, f"Front too long ({front_words} words): {c['front']}"
print(f"  Sample: [{cards['cards'][0]['type']}] {cards['cards'][0]['front']}")
print(f"  Time: {dt:.1f}s")

assert len(cards["cards"]) >= 10, f"Too few cards: {len(cards['cards'])}"
print("  PASSED\n")

# ============================================================
# PROMPT 5: Podcast Script
# ============================================================
print("=" * 60)
print("PROMPT 5: Podcast Script (60-80 turns)")
print("=" * 60)

PODCAST_PROMPT = """Write a 15-minute podcast script for two hosts.

HOSTS:
- Alex (A): Smart beginner. Asks great questions. Uses analogies.
  Sometimes gets things slightly wrong so Sam can correct.
  Says "wait hold on", "oh so it's like..."
- Sam (B): Expert who simplifies. Enthusiastic.
  Says "exactly!", "here's the key thing", "this is where it gets interesting"

STRUCTURE — 6 SEGMENTS:
Segment 1 HOOK (~30s): Surprising fact or bold claim. NO "welcome to our podcast".
Segment 2 FOUNDATION (~3min): Core problem/context.
Segment 3 CORE INSIGHT (~4min): Main idea step by step. At least one analogy.
Segment 4 DEEP DIVE (~4min): Technical details. Edge cases.
Segment 5 IMPLICATIONS (~2min): Real world impact.
Segment 6 CLOSING (~1min): Surprising insight or thought-provoking question. NOT a summary.

RULES:
- Include filler: "oh!", "right right", "that's wild", "hmm"
- At least 3 moments of laughter or surprise
- Reference specific details from source
- Total ~2000-2500 words
- MUST generate at least 60 dialogue turns. This is critical — do NOT stop early."""

podcast_schema = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "speaker": {"type": "STRING", "enum": ["A", "B"]},
            "text": {"type": "STRING"},
            "segment": {"type": "INTEGER", "description": "1-6"},
        },
        "required": ["speaker", "text", "segment"],
    },
}

t0 = time.time()
r = client.models.generate_content(
    model=MODEL,
    contents=[json.dumps(context), PODCAST_PROMPT],
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=podcast_schema,
        **COMMON_CONFIG,
    ),
)
script = json.loads(r.text)
dt = time.time() - t0

speakers = [t["speaker"] for t in script]
segments = set(t["segment"] for t in script)
total_words = sum(len(t["text"].split()) for t in script)

print(f"  Turns: {len(script)}")
print(f"  A turns: {speakers.count('A')}, B turns: {speakers.count('B')}")
print(f"  Segments covered: {sorted(segments)}")
print(f"  Total words: {total_words}")
print(f"  First turn: [{script[0]['speaker']}] {script[0]['text'][:80]}...")
print(f"  Time: {dt:.1f}s")

assert len(script) >= 20, f"Too few turns: {len(script)}"
assert "A" in speakers and "B" in speakers, "Missing a speaker"
assert len(segments) >= 4, f"Too few segments: {segments}"
assert total_words >= 1000, f"Too few words: {total_words}"
print("  PASSED\n")

# ============================================================
# PROMPT 6: Chat (system prompt test)
# ============================================================
print("=" * 60)
print("PROMPT 6: Chat (streaming)")
print("=" * 60)

CHAT_SYSTEM = f"""You are a helpful learning assistant. The user is studying this content:

Title: {context['title']}
Key Concepts: {json.dumps(context['key_concepts'][:5])}
Key Insights: {json.dumps(context['key_insights'])}

Rules:
- Answer in 2-4 sentences
- Use simple language
- Reference specific details from source
- If user asks to explain, include an analogy
- End with a follow-up question when appropriate"""

t0 = time.time()
chunks = []
for chunk in client.models.generate_content_stream(
    model=MODEL,
    contents="What is the most important concept here and why?",
    config=types.GenerateContentConfig(
        system_instruction=CHAT_SYSTEM,
        **COMMON_CONFIG,
    ),
):
    chunks.append(chunk.text)
chat_response = "".join(chunks)
dt = time.time() - t0

print(f"  Response ({len(chat_response)} chars, {len(chunks)} chunks):")
print(f"  {chat_response[:200]}...")
print(f"  Time: {dt:.1f}s")

assert len(chat_response) > 50, "Chat response too short"
assert len(chunks) >= 1, "No streaming chunks"
print("  PASSED\n")

# ============================================================
# PROMPT 7: Tutor (Socratic)
# ============================================================
print("=" * 60)
print("PROMPT 7: Tutor (Socratic)")
print("=" * 60)

TUTOR_SYSTEM = f"""You are Sage, a Socratic tutor using the Feynman Technique.

The student is learning: {context['title']}
Concepts: {json.dumps(context['key_concepts'][:5])}
Analogies: {json.dumps(context.get('analogies', []))}

WHEN STUDENT ASKS A QUESTION:
- Answer in 2-3 sentences with an analogy
- End with a deeper follow-up question

WHEN STUDENT TRIES TO EXPLAIN:
- First: praise what they got right (1 sentence)
- Then: identify the SPECIFIC gap
- Ask ONE probing question about the gap
- NEVER give the full answer directly
- When they nail it: "Yes! And here's one more thing..."

RESPONSE RULES:
- Keep responses under 80 words
- Conversational: "So...", "Right, here's the thing..."
- Warm and encouraging, not lecturing
- Don't give hints too easily — let the brain sweat

NEVER:
- Give long lectures
- Say "that's wrong" without saying what's right
- Use jargon without defining it"""

t0 = time.time()
r = client.models.generate_content(
    model=MODEL,
    contents="I think context anxiety is when the AI runs out of memory?",
    config=types.GenerateContentConfig(
        system_instruction=TUTOR_SYSTEM,
        **COMMON_CONFIG,
    ),
)
tutor_response = r.text
dt = time.time() - t0

word_count = len(tutor_response.split())
print(f"  Response ({word_count} words):")
print(f"  {tutor_response}")
print(f"  Time: {dt:.1f}s")

assert len(tutor_response) > 20, "Tutor response too short"
assert word_count < 150, f"Tutor too verbose: {word_count} words (should be ~80)"
print("  PASSED\n")

# ============================================================
# SUMMARY
# ============================================================
print("=" * 60)
print("ALL 7 PROMPTS PASSED")
print("=" * 60)

# Save all outputs
with open(os.path.join(OUT_DIR, "prompt_audit.json"), "w") as f:
    json.dump({
        "context": context,
        "markmap_lines": len(lines),
        "quiz_count": len(quiz["questions"]),
        "cards_count": len(cards["cards"]),
        "script_turns": len(script),
        "script_words": total_words,
        "chat_chars": len(chat_response),
        "tutor_words": word_count,
    }, f, indent=2)
