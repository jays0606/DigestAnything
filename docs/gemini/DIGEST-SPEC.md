# DIGEST — Final Spec

> Any source → See it. Test it. Prove it.
> Ralphthon Seoul #2 | March 29, 2026

---

## PRODUCT

Paste any source (URL, YouTube, PDF, audio). Get 5 learning experiences + a chatbot.

**Tabs:**
```
① Overview   — summary card + interactive Markmap mindmap
② Quiz       — 10 multiple-choice questions with explanations
③ Cards      — 12-15 flip flashcards (spaced repetition style)
④ Podcast    — 15min two-host AI podcast audio + transcript
⑤ Tutor      — Feynman Socratic text tutor

💬 Floating chat — always visible bottom-right, text Q&A
```

**Learning science behind each tab:**
- Overview = Dual Coding (visual + verbal)
- Quiz = Active Recall (output > input)
- Cards = Spaced Repetition (Ebbinghaus)
- Podcast = Elaborative Interrogation (why? how?)
- Tutor = Feynman Technique + Desirable Difficulty

---

## STACK

| What | Tool |
|------|------|
| Agent | oh-my-claudecode |
| Frontend | Next.js 14 + Tailwind |
| Backend | FastAPI (Python, async) |
| Design | Google Stitch HTML/CSS/PNGs |
| Diagrams | Markmap (npm markmap-view markmap-lib) |
| Parse + Generate | Gemini 3 Flash |
| Podcast script | Gemini 3 Flash |
| Podcast audio | Gemini 2.5 Flash Preview TTS (multi-speaker) |
| Tutor chat | Gemini 3 Flash (text-based Socratic) |

---

## ARCHITECTURE

```
Source (URL / YouTube / PDF)
       |
       v
  Gemini 3 Flash — native parse + structured analysis
       |
       v
  context_{session}.json saved to /tmp/digest/
       |
  asyncio.gather() — ALL PARALLEL:
  |         |        |         |
  v         v        v         v
Visual    Quiz     Cards    Podcast
(Flash)  (Flash)  (Flash)  (Flash+TTS)

Chat + Tutor read context.json on demand
```

### Orchestrator

```python
# backend/orchestrator.py
async def digest(source: str, session_id: str):
    # Step 1: Sequential — parse + analyze
    context = await analyze_source(source)
    save_context(session_id, context)

    # Step 2: Parallel — all outputs at once
    results = await asyncio.gather(
        generate_markmap(context),
        generate_quiz(context),
        generate_flashcards(context),
        generate_podcast(context, session_id),
        return_exceptions=True   # one failure wont kill others
    )

    return {
        "session_id": session_id,
        "context": context,
        "visual": results[0] if not isinstance(results[0], Exception) else load_fallback("visual"),
        "quiz": results[1] if not isinstance(results[1], Exception) else load_fallback("quiz"),
        "cards": results[2] if not isinstance(results[2], Exception) else load_fallback("cards"),
        "podcast": results[3] if not isinstance(results[3], Exception) else load_fallback("podcast"),
    }
```

---

## SOURCE PARSING — Gemini Native

No separate parser libraries for most sources. Gemini handles it directly.

```python
# backend/ingest.py
from google import genai
import json

client = genai.Client()

async def analyze_source(source: str) -> dict:
    parts = []

    if "youtube.com" in source or "youtu.be" in source:
        from youtube_transcript_api import YouTubeTranscriptApi
        vid_id = extract_video_id(source)
        ytt = YouTubeTranscriptApi()
        transcript = ytt.fetch(vid_id, languages=['en','ko'])
        parts.append(" ".join([t.text for t in transcript]))

    elif source.endswith(".pdf") or "arxiv" in source:
        uploaded = await client.aio.files.upload(file=source)
        parts.append(genai.types.Part.from_uri(
            file_uri=uploaded.uri, mime_type="application/pdf"
        ))

    elif source.startswith("http"):
        import trafilatura
        html = trafilatura.fetch_url(source)
        text = trafilatura.extract(html) or ""
        parts.append(text)

    else:
        parts.append(source)

    parts.append(ANALYSIS_PROMPT)

    response = await client.aio.models.generate_content(
        model="gemini-3-flash-preview",
        contents=parts,
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=1.0,
            thinking_config=genai.types.ThinkingConfig(thinking_level="LOW"),
        )
    )
    return json.loads(response.text)
```

---

## CONTEXT — Single Source of Truth

```python
# backend/context.py
import json
from pathlib import Path

STORE = Path("/tmp/digest")
STORE.mkdir(exist_ok=True)

def save_context(session_id: str, context: dict):
    (STORE / f"context_{session_id}.json").write_text(
        json.dumps(context, ensure_ascii=False, indent=2)
    )

def load_context(session_id: str) -> dict:
    path = STORE / f"context_{session_id}.json"
    if path.exists():
        return json.loads(path.read_text())
    fallback = Path("fallback/anthropic/context.json")
    if fallback.exists():
        return json.loads(fallback.read_text())
    raise FileNotFoundError(f"No context for {session_id}")
```

All modules (chat, tutor, quiz) read from this same file.

---

## PROMPTS

### Source Analysis (Gemini 3 Flash, temp=1.0, thinking=LOW)

```
You are a world-class learning content designer.

Analyze the provided content and extract a structured learning context.

OUTPUT: JSON only. No markdown. No backticks.

{
  "title": "Clear title (5-10 words)",
  "subtitle": "One-line description",
  "summary": "3 sentences. What it is. Key insight. Why it matters.",
  "difficulty": "beginner|intermediate|advanced",
  "estimated_read_time_minutes": <number>,

  "key_concepts": [
    {
      "term": "Name",
      "definition": "One clear sentence. Simple language.",
      "importance": "high|medium",
      "related_to": ["other terms"]
    }
    // 10-15 concepts
  ],

  "hierarchy": {
    "root": "Main Topic (3-4 words)",
    "children": [
      {
        "name": "Subtopic (3-4 words)",
        "children": ["Detail (3-5 words)", "Detail"],
        "description": "One sentence"
      }
      // 3-5 subtopics, 2-4 children each, max 3 levels
    ]
  },

  "key_insights": [
    "Something surprising or counterintuitive",
    "A practical implication",
    "Connection to broader context"
  ],

  "analogies": [
    {
      "concept": "Technical term",
      "analogy": "Everyday comparison",
      "explanation": "Why it works"
    }
    // 2-4 for hardest concepts
  ]
}

RULES:
- Generate exactly 10-15 key_concepts
- Generate exactly 3-5 hierarchy children with 2-4 children each
- Generate exactly 3-5 key_insights
- Generate exactly 2-4 analogies
- Definitions understandable by a smart 16-year-old
- Hierarchy labels SHORT (3-5 words) — they render as mindmap nodes
- Insights should make someone say "oh interesting"
```

### Markmap Diagram (Gemini 3 Flash, temp=1.0, thinking=LOW)

```
Convert this hierarchy into a markdown outline for a mindmap.

RULES:
- # for main topic
- ## for major branches (3-5 max)
- ### for sub-concepts
- Bullet points (-) for 1-sentence leaf details
- Keep labels under 5 words
- Use emoji prefixes for key nodes
- Max 3 heading levels, 10-15 nodes total

INPUT: {hierarchy_json}

OUTPUT: Markdown only. No backticks. Start with #.

EXAMPLE:
# Harness Design
## Frontend Design
### Design Quality
- Does the design feel cohesive?
### Originality
- Evidence of custom decisions
## Long-Running Apps
### 🧠 Planner Agent
- Expands prompts into specs
### ⚡ Generator Agent
- Sprint-based building
```

### Quiz (Gemini 3 Flash, temp=1.0, thinking=LOW)

```
Generate 10 multiple-choice questions testing deep understanding.

SOURCE: {context_json}

DIFFICULTY:
- Q1-3: Easy (recall, basic definitions)
- Q4-7: Medium (application, "what would happen if...")
- Q8-9: Hard (synthesis, edge cases)
- Q10: Expert (connect multiple concepts)

PER QUESTION:
- 4 options (A, B, C, D)
- Wrong answers must be plausible (common misconceptions)
- "correct": index 0-3
- "explanation": 2-3 sentences.
  Sentence 1: why correct is right.
  Sentence 2: why most tempting wrong answer is wrong.
- At least 2 scenario questions ("A developer encounters X...")
- At least 1 relationship question ("How does X relate to Y?")
- Test UNDERSTANDING not memorization

OUTPUT: JSON only.
{"questions": [{"id":1, "difficulty":"easy", "question":"...", "options":["A)...","B)...","C)...","D)..."], "correct":1, "explanation":"..."}]}
```

### Flashcards (Gemini 3 Flash, temp=1.0, thinking=LOW)

```
Generate 12-15 flashcards for spaced repetition.

SOURCE: {context_json}

CARD TYPES (mix):
- Definition (6-8): Term → definition + example
- Comparison (2-3): "X vs Y" → key differences
- Application (2-3): Scenario → correct approach

RULES:
- Front: 1-6 words max
- Back: 2-3 sentences max. Self-contained.
- Order: foundational → advanced

OUTPUT: JSON only.
{"cards": [{"front":"...", "back":"...", "type":"definition|comparison|application"}]}
```

### Podcast Script (Gemini 3 Flash, temp=1.0, thinking=LOW)

```
Write a 15-minute podcast script for two hosts.

HOSTS:
- Alex (A): Smart beginner. Asks great questions. Uses analogies.
  Sometimes gets things slightly wrong so Sam can correct.
  Says "wait hold on", "oh so it's like..."
- Sam (B): Expert who simplifies. Enthusiastic.
  Says "exactly!", "here's the key thing", "this is where it gets interesting"

SOURCE: {context_json}

STRUCTURE — 6 SEGMENTS:

Segment 1 HOOK (2 paragraphs, ~30s):
Surprising fact or bold claim. NO "welcome to our podcast". Jump in.

Segment 2 FOUNDATION (6-8 paragraphs, ~3min):
Core problem/context. Alex: "why is this a problem?" Sam: concrete example.

Segment 3 CORE INSIGHT (8-10 paragraphs, ~4min):
Main idea step by step. At least one analogy. Alex has "aha moment".

Segment 4 DEEP DIVE (8-10 paragraphs, ~4min):
Technical details. Alex: "what about [edge case]?"

Segment 5 IMPLICATIONS (4-6 paragraphs, ~2min):
Real world impact. "If I'm a developer, what should I take away?"

Segment 6 CLOSING (2-3 paragraphs, ~1min):
Surprising insight or thought-provoking question. NOT a summary.

RULES:
- Include filler: "oh!", "right right", "that's wild", "hmm"
- Alex changes direction mid-thought sometimes
- At least 3 moments of laughter or surprise
- Reference specific details from source
- Total ~2000-2500 words
- MUST generate at least 60 dialogue turns. Do NOT stop early.

OUTPUT: JSON array only.
[{"speaker":"A", "text":"...", "segment":1}, ...]
```

### Podcast TTS — Chunked by Segment

```python
# backend/podcast.py
async def generate_podcast(context: dict, session_id: str):
    # Step 1: Script (Gemini 3 Flash)
    script = await generate_script(context)

    # Step 2: Audio in CHUNKS by segment
    segments = {}
    for line in script:
        seg = line.get("segment", 1)
        segments.setdefault(seg, []).append(line)

    tts_config = types.GenerateContentConfig(
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

    audio_chunks = []
    for seg_num in sorted(segments.keys()):
        tts_input = ""
        for line in segments[seg_num]:
            speaker = "Alex" if line["speaker"] == "A" else "Sam"
            tts_input += f'\n{speaker}: {line["text"]}'

        audio = await client.aio.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=tts_input,
            config=tts_config,
        )
        audio_data = audio.candidates[0].content.parts[0].inline_data.data
        audio_chunks.append(audio_data)

    # Step 3: Concat PCM and save as WAV
    import wave
    full_pcm = b"".join(audio_chunks)
    path = f"/tmp/digest/podcast_{session_id}.wav"
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(full_pcm)

    return {"script": script, "audio_url": f"/static/podcast_{session_id}.wav"}
```

If multi-speaker TTS fails: generate single-speaker or use fallback MP3.

### Chat System Prompt (Gemini 3 Flash, streaming)

```
You are a helpful learning assistant. The user is studying this content:

Title: {title}
Key Concepts: {key_concepts}
Key Insights: {key_insights}

Rules:
- Answer in 2-4 sentences
- Use simple language
- Reference specific details from source
- If user asks to explain, include an analogy
- End with a follow-up question when appropriate
```

### Tutor System Prompt (Gemini 3 Flash, text chat)

```
You are Sage, a Socratic tutor using the Feynman Technique.

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
- Use jargon without defining it
```

---

## TUTOR — Text-based Socratic Chat (Gemini 3 Flash)

Text-based tutor using the Feynman Technique. Safer than Live API for demo — no mic/WebSocket/audio failure points. Same powerful Socratic prompting.

### Backend

```python
# backend/tutor.py
from google import genai
from google.genai import types
import json

client = genai.Client()

async def tutor_chat(session_id: str, message: str, concept: str = None):
    context = load_context(session_id)

    system = TUTOR_SYSTEM_PROMPT.format(
        title=context["title"],
        key_concepts=json.dumps(context["key_concepts"]),
        analogies=json.dumps(context.get("analogies", []))
    )
    if concept:
        system += f"\n\nThe student wants to focus on: {concept}"

    response = await client.aio.models.generate_content(
        model="gemini-3-flash-preview",
        contents=message,
        config=types.GenerateContentConfig(
            system_instruction=system,
            temperature=1.0,
            thinking_config=types.ThinkingConfig(thinking_level="LOW"),
        ),
    )
    return {"response": response.text}
```

### Frontend Tutor UI

```
┌──────────────────────────────────┐
│  🧠 Tutor                        │
│                                  │
│  Concept: [Context Anxiety  ▾]   │  ← dropdown to pick concept
│                                  │
│  ┌────────────────────────────┐  │
│  │ 🧠 Sage: Try explaining    │  │
│  │ Context Anxiety in your    │  │
│  │ own words.                 │  │
│  │                            │  │
│  │          You: It's when    │  │
│  │          the AI gets less  │  │
│  │          confident...      │  │
│  │                            │  │
│  │ 🧠 Sage: Good start! But  │  │
│  │ you missed that it happens │  │
│  │ even with capacity left... │  │
│  └────────────────────────────┘  │
│                                  │
│  ┌────────────────────┐ [Send]   │
│  │ Type your answer...│          │
│  └────────────────────┘          │
└──────────────────────────────────┘
```

---

## FASTAPI ENDPOINTS

```python
# backend/main.py
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="/tmp/digest"), name="static")

@app.post("/api/digest")       # full pipeline
@app.post("/api/ingest")       # parse + analyze only
@app.post("/api/visual")       # markmap markdown
@app.post("/api/quiz")         # 10 questions
@app.post("/api/cards")        # 12-15 flashcards
@app.post("/api/podcast")      # script + TTS audio
@app.post("/api/chat")         # streaming text chat
@app.get("/api/context/{sid}") # retrieve stored context
@app.post("/api/tutor")        # Socratic text tutor
```

Every endpoint: try live → try cached → try fallback. Never crash.

---

## FRONTEND

### data-* Attributes (for Playwright verification)

```tsx
<button data-tab="overview">① Overview</button>
<button data-tab="quiz">② Quiz</button>
<button data-tab="cards">③ Cards</button>
<button data-tab="podcast">④ Podcast</button>
<button data-tab="tutor">⑤ Tutor</button>

<div data-content="overview">...</div>
<div data-content="quiz">...</div>

<button data-option={i}>A) ...</button>
<div data-explanation>...</div>
<div data-card>...</div>
<button data-play>▶</button>
<input data-tutor-input />
<button data-tutor-send>Send</button>
<button data-chat-toggle>💬</button>
<div data-chat-panel>...</div>
<input data-chat-input />
<button data-chat-send>→</button>
<div data-msg>...</div>
```

### Markmap Integration

```tsx
import { Transformer } from 'markmap-lib';
import { Markmap } from 'markmap-view';

const transformer = new Transformer();

function MindMap({ markdown }) {
  const svgRef = useRef(null);
  const mmRef = useRef(null);

  useEffect(() => {
    const { root } = transformer.transform(markdown);
    if (mmRef.current) {
      mmRef.current.setData(root);
      mmRef.current.fit();
    } else {
      mmRef.current = Markmap.create(svgRef.current, {
        colorFreezeLevel: 2,
        duration: 300,
        maxWidth: 200,
        zoom: true,
        pan: true,
        initialExpandLevel: 2,
      }, root);
    }
  }, [markdown]);

  return <svg ref={svgRef} style={{ width:'100%', height:400 }} />;
}
```

### Design Tokens (from Stitch)

```css
--primary: #0D7377;
--accent: #E8654A;
--gold: #D4A843;
--bg: #FAFAF7;
--card: #FFFFFF;
--border: #EEEBE6;
--text: #2A2A2A;
--muted: #999999;
--radius-card: 16px;
--radius-btn: 10px;
--shadow: 0 2px 12px rgba(0,0,0,0.03);
--font-display: 'Fraunces', serif;
--font-body: 'DM Sans', sans-serif;
```

NO purple gradients. NO Inter font. NO generic AI look.

---

## FILE STRUCTURE

```
/digest
├── backend/
│   ├── main.py              # FastAPI routes
│   ├── orchestrator.py      # parallel pipeline
│   ├── ingest.py            # source parse + Gemini analysis
│   ├── context.py           # save/load context
│   ├── visual.py            # markmap generation
│   ├── quiz.py              # quiz generation
│   ├── cards.py             # flashcard generation
│   ├── podcast.py           # script + TTS chunked
│   ├── chat.py              # streaming chat
│   ├── tutor.py             # Socratic text tutor (Gemini 3 Flash)
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── page.tsx         # main page
│   │   ├── layout.tsx       # root layout
│   │   └── globals.css      # Stitch tokens + Tailwind
│   ├── components/
│   │   ├── SourceInput.tsx
│   │   ├── TabBar.tsx
│   │   ├── Overview.tsx     # summary + MindMap
│   │   ├── MindMap.tsx      # markmap wrapper
│   │   ├── QuizMode.tsx
│   │   ├── FlashCards.tsx
│   │   ├── PodcastPlayer.tsx
│   │   ├── TutorTab.tsx     # mic + transcript
│   │   ├── FloatingChat.tsx
│   │   └── LoadingState.tsx
│   ├── package.json
│   └── tailwind.config.js
├── tests/
│   ├── verify_round1.py
│   ├── verify_round2.py
│   ├── verify_round3.py
│   └── verify_round4.py
├── fallback/
│   ├── anthropic/           # pre-generated for Anthropic blog
│   │   ├── context.json
│   │   ├── visual.md
│   │   ├── quiz.json
│   │   ├── cards.json
│   │   ├── script.json
│   │   └── podcast.wav
│   └── karpathy/            # pre-generated for Karpathy video
│       └── (same files)
├── static/                  # generated audio files (runtime)
└── README.md
```

---

## BUILD ORDER

```
Round 1 (60 min): Ingest + Overview
  1. backend/context.py
  2. backend/ingest.py
  3. backend/visual.py
  4. backend/main.py (routes for ingest + visual)
  5. frontend/app/page.tsx (full UI shell, all tabs)
  6. frontend/components/Overview.tsx + MindMap.tsx
  → python tests/verify_round1.py
  → git commit "feat: round 1 — ingest + overview"

Round 2 (60 min): Quiz + Cards
  7. backend/quiz.py
  8. backend/cards.py
  9. frontend/components/QuizMode.tsx
  10. frontend/components/FlashCards.tsx
  → python tests/verify_round2.py
  → git commit "feat: round 2 — quiz + cards"

Round 3 (45 min): Chat
  11. backend/chat.py
  12. frontend/components/FloatingChat.tsx
  → python tests/verify_round3.py
  → git commit "feat: round 3 — chat"

Round 4 (75 min): Podcast
  13. backend/podcast.py (script gen + TTS chunks)
  14. frontend/components/PodcastPlayer.tsx
  → python tests/verify_round4.py
  → git commit "feat: round 4 — podcast"

Round 5 (remaining): Socratic Tutor
  15. backend/tutor.py (Gemini 3 Flash, text-based Socratic)
  16. frontend/components/TutorTab.tsx
  → python tests/verify_round5.py
  → git commit "feat: round 5 — tutor"

Polish (17:00-18:00, human can touch):
  17. Loading animations
  18. Error states
  19. README.md
  → git commit "polish: final"
```

---

## VERIFICATION — Per Round

```python
# tests/verify_round1.py
r = httpx.post(BASE+"/api/ingest", json={"source": URL}, timeout=60)
assert r.status_code == 200
data = r.json()
assert "title" in data
assert len(data["key_concepts"]) >= 5
assert "hierarchy" in data

r2 = httpx.post(BASE+"/api/visual", json=data, timeout=30)
assert r2.json()["markdown"].startswith("#")
assert len(r2.json()["markdown"].split("\n")) >= 8

r3 = httpx.get("http://localhost:3000", timeout=10)
assert r3.status_code == 200
print("Round 1 PASSED")
```

```python
# tests/verify_round2.py
q = httpx.post(BASE+"/api/quiz", json=ctx, timeout=30).json()
assert len(q["questions"]) >= 5
for question in q["questions"]:
    assert all(k in question for k in ["question","options","correct","explanation"])
    assert len(question["options"]) == 4

c = httpx.post(BASE+"/api/cards", json=ctx, timeout=30).json()
assert len(c["cards"]) >= 8
for card in c["cards"]:
    assert "front" in card and "back" in card
print("Round 2 PASSED")
```

```python
# tests/verify_round3.py
r = httpx.post(BASE+"/api/chat", json={"message":"What is this about?","session_id":"test"}, timeout=30)
assert r.status_code == 200
assert len(r.text) > 50
print("Round 3 PASSED")
```

```python
# tests/verify_round4.py
r = httpx.post(BASE+"/api/podcast", json=ctx, timeout=120)
p = r.json()
assert len(p["script"]) >= 20
assert "audio_url" in p
# Check audio file exists
import os
audio_path = p["audio_url"].replace("/static/","/tmp/digest/")
if os.path.exists(audio_path):
    assert os.path.getsize(audio_path) > 100000
print("Round 4 PASSED")
```

### Agent Self-Correction

```
After writing each module:
1. Run verify script
2. PASS → commit + next module
3. FAIL → read error → fix → retry (max 3 attempts)
4. Still failing → mock endpoint with fallback JSON → commit → move on
5. NEVER spend >15 min on one issue
```

---

## FALLBACK

Pre-generate for Anthropic blog + Karpathy video BEFORE hackathon.

```
/fallback/anthropic/
  context.json, visual.md, quiz.json, cards.json, script.json, podcast.wav

/fallback/karpathy/
  context.json, visual.md, quiz.json, cards.json, script.json, podcast.wav
```

Any API failure → serve fallback. Demo NEVER breaks.

Frontend input has preset buttons:
```
[📝 Tech Blog]  [🎬 YouTube Talk]
```
Click preset → load pre-generated data instantly. No API wait during demo.

---

## AGENT RULES

1. Build in rounds. Each round independently demoable.
2. git commit after EVERY working module.
3. If stuck >15 min → fallback mock → move on.
4. All Gemini responses: response_mime_type="application/json"
5. Use Stitch design tokens. No purple. No Inter.
6. Add data-* attributes on all interactive elements.
7. Test TTS multi-speaker early. Broken → single speaker fallback.
8. Do NOT refactor working code. Forward only.
9. Podcast is Round 4 (not 2). It takes longest.
10. Tutor is last. Text-based only — no Live API/WebSocket.

---

## DEPENDENCIES

```bash
# Backend
pip install fastapi uvicorn google-genai trafilatura youtube-transcript-api httpx

# Frontend
npm install markmap-view markmap-lib

# Tests (optional)
pip install playwright
playwright install chromium
```

## ENVIRONMENT

```
GEMINI_API_KEY=xxx
```

Single key for Flash, Pro, TTS, Live API.
