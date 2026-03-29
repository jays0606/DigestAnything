# DigestAnything — Agent Execution Guide

> Everything the agent needs to build, test, and verify this project.

## Pre-validated: What Already Works

### Models (2 total)

| Model | Used For |
|-------|----------|
| `gemini-3-flash-preview` | All 7 text prompts (analysis, markmap, quiz, cards, podcast script, chat, tutor) |
| `gemini-2.5-flash-preview-tts` | Podcast audio only (multi-speaker) |

### Uniform Config

```python
config = types.GenerateContentConfig(
    temperature=1.0,
    thinking_config=types.ThinkingConfig(thinking_level="LOW"),
    response_mime_type="application/json",  # for structured outputs
    # response_schema=...                   # for quiz, cards, podcast script
)
```

No `max_output_tokens`. No Pro model. No voice/live API.

### Prompts (7/7 verified, all passing)

| # | Prompt | Output | Tested |
|---|--------|--------|--------|
| 1 | Source Analysis | JSON: title, 10-15 concepts, hierarchy, insights, analogies | 9.2s |
| 2 | Markmap | Markdown (# ## ### -) — plain text, no schema | 8.4s |
| 3 | Quiz | JSON: 10 MCQs, difficulty enum, 4 options, correct 0-3 | 10.8s |
| 4 | Flashcards | JSON: 12-15 cards, type enum (definition/comparison/application) | 7.0s |
| 5 | Podcast Script | JSON array: 60+ turns, speaker A/B enum, segment 1-6 | 21.0s |
| 6 | Chat | Streaming text, references source content | 4.4s |
| 7 | Tutor | Socratic text response, stays concise | 3.0s |

### TTS Pipeline (verified)

- Chunked by segment (3-6 chunks)
- Multi-speaker: Kore (Alex/beginner) + Charon (Sam/expert)
- Speaker format in TTS input: `Alex: text` / `Sam: text`
- Output: raw PCM → WAV (24000Hz, 16-bit mono)
- 3 segments = ~114s audio in ~60s generation

### YouTube Transcript (verified)

```python
ytt = YouTubeTranscriptApi()
transcript = ytt.fetch(vid_id, languages=['en', 'ko'])
text = " ".join([t.text for t in transcript])
```

Pre-cached transcript available at `tests/samples/youtube_transcript.json`.

---

## How to Run

### Start Backend

```bash
export $(cat .env | xargs)
uv run uvicorn backend.main:app --reload --port 8000
```

### Start Frontend

```bash
cd frontend
npm run dev  # port 3000
```

### Run Tests

```bash
# Gemini API validation (no servers needed)
export $(cat .env | xargs)
uv run python tests/run_all.py

# App endpoint verification (requires both servers running)
uv run python tests/verify_round1.py   # ingest + visual + frontend
uv run python tests/verify_round2.py   # quiz + cards
uv run python tests/verify_round3.py   # chat + tutor
uv run python tests/verify_round4.py   # podcast + TTS
```

---

## Verification Matrix

### Round 1: Ingest + Overview

| Endpoint | Method | Assertions |
|----------|--------|------------|
| `/api/ingest` | POST `{"source": URL}` | 200, has title, 5+ key_concepts, hierarchy, key_insights, summary |
| `/api/visual` | POST context JSON | 200, markdown starts with `#`, 8+ non-empty lines |
| `localhost:3000` | GET | 200, HTML >500 chars |
| `/api/context/{sid}` | GET | 200 if session exists |

### Round 2: Quiz + Cards

| Endpoint | Method | Assertions |
|----------|--------|------------|
| `/api/quiz` | POST context JSON | 200, 5+ questions, each: question/options(4)/correct(0-3)/explanation |
| `/api/cards` | POST context JSON | 200, 8+ cards, each: front/back/type enum |

### Round 3: Chat + Tutor

| Endpoint | Method | Assertions |
|----------|--------|------------|
| `/api/chat` | POST `{"message", "session_id"}` | 200, response >30 chars |
| `/api/tutor` | POST `{"message", "session_id"}` | 200, `response` key, >20 chars |
| `/api/tutor` | POST with `concept` param | 200, Socratic response for specific concept |

### Round 4: Podcast

| Endpoint | Method | Assertions |
|----------|--------|------------|
| `/api/podcast` | POST context JSON | 200, script 20+ turns, 2 speakers, 3+ segments, audio_url |
| Audio file | Check `/tmp/digest/` | Exists, >100KB |

---

## Reference Files

| File | Purpose |
|------|---------|
| `SPEC.md` | Full product spec with all prompts, architecture, code samples |
| `CLAUDE.md` | Agent build instructions — models, design tokens, rules |
| `docs/stitch/DESIGN.md` | "Cognitive Sanctuary" design system philosophy |
| `docs/stitch/code.html` | Reference Tailwind config + HTML components |
| `docs/stitch/screen.png` | Visual reference (Flashcards view) |
| `docs/gemini/*.md` | Gemini API patterns (text gen, TTS, PDF, prompting) |
| `tests/samples/*.json` | Pre-generated context, quiz, cards, transcript samples |

---

## Build Order

```
Round 1 → backend/context.py, ingest.py, visual.py, main.py
         → frontend/ scaffold + Overview + MindMap
         → verify_round1.py

Round 2 → backend/quiz.py, cards.py
         → QuizMode.tsx, FlashCards.tsx
         → verify_round2.py

Round 3 → backend/chat.py, tutor.py
         → FloatingChat.tsx, TutorTab.tsx
         → verify_round3.py

Round 4 → backend/podcast.py
         → PodcastPlayer.tsx
         → verify_round4.py
```

Each round is independently demoable. Commit after each.
