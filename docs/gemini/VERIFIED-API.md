# Gemini API — Verified Reference

> All code below is **tested and passing** with our API key as of 2026-03-29.
> Run `export $(cat .env | xargs) && uv run python tests/run_all.py` to re-verify.

---

## Models (2 total)

| Model ID | Purpose | Verified |
|----------|---------|----------|
| `gemini-3-flash-preview` | All text generation (ingest, quiz, cards, podcast script, chat, tutor, markmap) | Yes |
| `gemini-2.5-flash-preview-tts` | Podcast audio only (multi-speaker) | Yes |

**No other models needed.** Everything runs on Flash.

---

## Unified Config

Every text generation call uses this config:

```python
from google import genai
from google.genai import types

client = genai.Client()  # reads GEMINI_API_KEY from env

config = types.GenerateContentConfig(
    temperature=1.0,                                          # Gemini 3 best practice — do NOT lower
    thinking_config=types.ThinkingConfig(thinking_level="LOW"), # fast + reliable
    response_mime_type="application/json",                     # for JSON outputs only
    response_schema=YOUR_SCHEMA,                               # for JSON outputs only
)
```

**Do NOT set:**
- `max_output_tokens` — let the model decide
- `temperature` below 1.0 — causes looping/degraded output on Gemini 3
- `top_p` / `top_k` — defaults are fine

---

## Prompt 1: Source Analysis

**Input:** Raw text (from URL, YouTube transcript, or PDF)
**Output:** Structured context JSON — the single source of truth for all other prompts

```python
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

ANALYSIS_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "title": {"type": "STRING"},
        "subtitle": {"type": "STRING"},
        "summary": {"type": "STRING"},
        "difficulty": {"type": "STRING", "enum": ["beginner", "intermediate", "advanced"]},
        "estimated_read_time_minutes": {"type": "INTEGER"},
        "key_concepts": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "term": {"type": "STRING"},
                    "definition": {"type": "STRING"},
                    "importance": {"type": "STRING", "enum": ["high", "medium"]},
                    "related_to": {"type": "ARRAY", "items": {"type": "STRING"}},
                },
                "required": ["term", "definition", "importance"],
            },
        },
        "hierarchy": {
            "type": "OBJECT",
            "properties": {
                "root": {"type": "STRING"},
                "children": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "name": {"type": "STRING"},
                            "children": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "description": {"type": "STRING"},
                        },
                        "required": ["name", "children"],
                    },
                },
            },
            "required": ["root", "children"],
        },
        "key_insights": {"type": "ARRAY", "items": {"type": "STRING"}},
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

# Usage
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=[source_text, ANALYSIS_PROMPT],
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=ANALYSIS_SCHEMA,
        temperature=1.0,
        thinking_config=types.ThinkingConfig(thinking_level="LOW"),
    ),
)
context = json.loads(response.text)
```

**Verified output:** 12 concepts, 3 hierarchy branches, 4 insights, 3 analogies. ~9s.

---

## Prompt 2: Markmap

**Input:** `context["hierarchy"]` JSON
**Output:** Plain markdown (no JSON, no schema)

```python
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

# Usage — NO response_mime_type, NO response_schema (plain text)
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=MARKMAP_PROMPT.format(hierarchy=json.dumps(context["hierarchy"])),
    config=types.GenerateContentConfig(
        temperature=1.0,
        thinking_config=types.ThinkingConfig(thinking_level="LOW"),
    ),
)
markdown = response.text
```

**Verified output:** Renders correctly with markmap-view (14 nodes, 3 branches). ~6s.

Frontend renders with:
```tsx
import { Transformer } from 'markmap-lib';
import { Markmap } from 'markmap-view';
const { root } = new Transformer().transform(markdown);
Markmap.create(svgRef, options, root);
```

---

## Prompt 3: Quiz

**Input:** Full context JSON
**Output:** 10 multiple-choice questions

```python
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

QUIZ_SCHEMA = {
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
                    "correct": {"type": "INTEGER"},
                    "explanation": {"type": "STRING"},
                },
                "required": ["id", "difficulty", "question", "options", "correct", "explanation"],
            },
        },
    },
    "required": ["questions"],
}
```

**Verified output:** 10 questions, correct difficulty distribution, 4 options each, valid `correct` index. ~11s.

---

## Prompt 4: Flashcards

**Input:** Full context JSON
**Output:** 12-15 flashcards

```python
CARDS_PROMPT = """Generate 12-15 flashcards for spaced repetition.

CARD TYPES (mix):
- Definition (6-8): Term → definition + example
- Comparison (2-3): "X vs Y" → key differences
- Application (2-3): Scenario → correct approach

RULES:
- Front: 1-6 words max
- Back: 2-3 sentences max. Self-contained.
- Order: foundational → advanced"""

CARDS_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "cards": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "front": {"type": "STRING"},
                    "back": {"type": "STRING"},
                    "type": {"type": "STRING", "enum": ["definition", "comparison", "application"]},
                },
                "required": ["front", "back", "type"],
            },
        },
    },
    "required": ["cards"],
}
```

**Verified output:** 14 cards (7 def, 3 comparison, 3 application). ~5s.

---

## Prompt 5: Podcast Script

**Input:** Full context JSON
**Output:** 60+ dialogue turns across 6 segments

```python
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
- MUST generate at least 60 dialogue turns. Do NOT stop early."""

PODCAST_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "speaker": {"type": "STRING", "enum": ["A", "B"]},
            "text": {"type": "STRING"},
            "segment": {"type": "INTEGER"},
        },
        "required": ["speaker", "text", "segment"],
    },
}
```

**Verified output:** 63 turns, all 6 segments, balanced A/B. ~21s.

---

## Prompt 6: Podcast TTS (multi-speaker, chunked)

**Input:** Script from Prompt 5, chunked by segment
**Output:** PCM audio → merged WAV

```python
TTS_CONFIG = types.GenerateContentConfig(
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

# Build TTS input per segment
for seg_num in sorted(segments.keys()):
    tts_input = ""
    for line in segments[seg_num]:
        speaker = "Alex" if line["speaker"] == "A" else "Sam"
        tts_input += f"\n{speaker}: {line['text']}"

    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=tts_input,
        config=TTS_CONFIG,
    )
    audio_data = response.candidates[0].content.parts[0].inline_data.data
    audio_chunks.append(audio_data)

# Merge PCM → WAV
import wave
merged_pcm = b"".join(audio_chunks)
with wave.open(path, "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(24000)
    wf.writeframes(merged_pcm)
```

**Verified output:** 3 segments → 114s audio (1.9min), 5.3MB WAV, 60s total TTS time.

**Voice options:** Kore (firm), Charon (informative). See `docs/gemini/speech-generation-tts.md` for all 30 voices.

---

## Prompt 7: Chat (streaming)

```python
CHAT_SYSTEM = """You are a helpful learning assistant. The user is studying this content:

Title: {title}
Key Concepts: {key_concepts}
Key Insights: {key_insights}

Rules:
- Answer in 2-4 sentences
- Use simple language
- Reference specific details from source
- If user asks to explain, include an analogy
- End with a follow-up question when appropriate"""

# Streaming usage
for chunk in client.models.generate_content_stream(
    model="gemini-3-flash-preview",
    contents=user_message,
    config=types.GenerateContentConfig(
        system_instruction=CHAT_SYSTEM.format(...),
        temperature=1.0,
        thinking_config=types.ThinkingConfig(thinking_level="LOW"),
    ),
):
    yield chunk.text
```

---

## Prompt 8: Tutor (Socratic)

```python
TUTOR_SYSTEM = """You are Sage, a Socratic tutor using the Feynman Technique.

The student is learning: {title}
Concepts: {key_concepts}
Analogies: {analogies}

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
```

---

## Source Parsing (tested)

### YouTube
```python
from youtube_transcript_api import YouTubeTranscriptApi
ytt = YouTubeTranscriptApi()
transcript = ytt.fetch(video_id, languages=["en", "ko"])
text = " ".join([t.text for t in transcript])
```
**Verified:** 2231 segments, 81K chars from demo video.

### Web URL
```python
import trafilatura
html = trafilatura.fetch_url(url)
text = trafilatura.extract(html)
```
**Verified:** 31K chars from Anthropic blog.

### PDF
```python
uploaded = client.files.upload(file=pdf_path)
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=[
        types.Part.from_uri(file_uri=uploaded.uri, mime_type="application/pdf"),
        prompt,
    ],
)
client.files.delete(name=uploaded.name)  # cleanup
```
**Verified:** 1.8MB PDF analyzed in 41s.

---

## Tests

```
tests/
├── test_00_setup.py            # API key + model listing
├── test_01_flash_text.py       # Flash: text + JSON + streaming
├── test_02_pro_text.py         # Pro: system instructions
├── test_03_pdf_upload.py       # PDF Files API + analysis
├── test_04_tts_single.py       # Single speaker → WAV
├── test_05_tts_multi.py        # Multi-speaker → WAV
├── test_06_youtube.py          # YouTube transcript extraction
├── test_07_web_content.py      # trafilatura + Gemini analysis
├── test_08_video_understanding.py  # Video upload + analysis
├── test_09_full_pipeline.py    # Ingest → context → quiz → cards
├── test_10_all_prompts.py      # All 7 prompts with response_schema
├── test_11_tts_chunked_podcast.py  # Script → chunk → TTS → merge WAV
├── run_all.py                  # Run all tests sequentially
└── samples/                    # Generated outputs (WAV, JSON, MD)
```

Run all: `export $(cat .env | xargs) && uv run python tests/run_all.py`
Run one: `export $(cat .env | xargs) && uv run python tests/test_10_all_prompts.py`
