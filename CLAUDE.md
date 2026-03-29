# DIGEST — Agent Instructions

> Any source → See it. Test it. Prove it.

## Project

DIGEST is a learning platform. Paste any URL/YouTube/PDF → get 5 AI-powered learning tabs + chatbot.

## Models

| Purpose | Model ID | Temp |
|---------|----------|------|
| Source analysis | `gemini-3-flash-preview` | 0.2 |
| Markmap visual | `gemini-3-flash-preview` | 0.2 |
| Quiz generation | `gemini-3-flash-preview` | 0.4 |
| Flashcard generation | `gemini-3-flash-preview` | 0.3 |
| Podcast script | `gemini-2.5-pro-preview-05-06` | 0.8 |
| Podcast TTS | `gemini-2.5-flash-preview-tts` | N/A |
| Chat | `gemini-3-flash-preview` | 0.7 |
| Tutor | `gemini-3-flash-preview` | 1.0 |

All models use `response_mime_type="application/json"` except TTS and streaming chat.

## Stack

- **Backend:** FastAPI (Python, async) — port 8000
- **Frontend:** Next.js 14 + Tailwind CSS — port 3000
- **Python env:** `uv` (not pip). Run `uv sync` to install.
- **Diagrams:** Markmap (`markmap-view`, `markmap-lib`)

## Design System — "The Cognitive Sanctuary" (from Google Stitch)

Full reference: `docs/stitch/DESIGN.md`, `docs/stitch/code.html`, `docs/stitch/screen.png`

### Philosophy
- **"Cognitive Sanctuary"** — premium, quiet space for intellectual growth
- **No-Line Rule:** NO 1px solid borders to define sections. Use tonal shifts + negative space instead
- **Tonal Layering** over structural lines for depth/hierarchy
- **Glassmorphism** on header: `rgba(248, 249, 250, 0.7)` + `backdrop-filter: blur(20px)`

### Colors (Tailwind extended)

```js
// tailwind.config.js — extend colors
{
  "primary": "#005bbf",              // Intelligence Blue
  "primary-container": "#1a73e8",    // Lighter blue for highlights
  "primary-fixed": "#d8e2ff",        // Very light blue
  "secondary": "#1b6d24",            // Success Green
  "secondary-container": "#a0f399",  // Light green (progress tracks)
  "tertiary": "#006875",             // Teal accent
  "surface": "#f8f9fa",              // Base background
  "surface-container-low": "#f3f4f5", // Secondary regions
  "surface-container-lowest": "#ffffff", // Content cards (highest focus)
  "surface-container-high": "#e7e8e9",  // Input fills
  "on-surface": "#191c1d",           // Primary text (NOT pure black)
  "on-surface-variant": "#414754",   // Muted text, labels
  "outline": "#727785",              // Input underlines
  "outline-variant": "#c1c6d6",      // Ghost borders (15% opacity only)
  "error": "#ba1a1a",
  "error-container": "#ffdad6",
}
```

### Typography

```
Fonts: Manrope (headlines) + Inter (body/labels)
Google Fonts: family=Manrope:wght@400;500;600;700;800&family=Inter:wght@400;500;600

Tailwind fontFamily:
  headline: ["Manrope"]
  body: ["Inter"]
  label: ["Inter"]

Headlines: tighter letter-spacing (-0.02em), magazine feel
Body: body-lg (1rem) for learning content
Labels: label-md (0.75rem), on-surface-variant color
```

### Key Component Patterns

- **Cards:** `rounded-xl` (12px), NO dividers, tonal background shift instead
- **Primary buttons:** Gradient `from-primary to-primary-container`, `rounded-full`, white text
- **Secondary buttons:** Transparent + ghost border (outline-variant at 15% opacity)
- **Input fields:** `surface-container-high` fill, bottom-only outline, 2px primary on focus
- **Progress bars:** `secondary` fill on `secondary-container` track, soft glow on tip
- **Shadows:** Tinted with `on-surface` at 6% opacity, 32-48px blur (diffused, natural)
- **Glass header:** Fixed, `surface` at 70% opacity + 20px backdrop blur

### Layout

- Sidebar (left, 256px) with navigation: Digest → Feynman → Quiz → Flashcards
- Progress stepper at top of main content
- Main content: max-w-4xl, centered
- Mobile: bottom nav bar replaces sidebar
- Material Symbols Outlined for icons

### Do NOT

- Use 1px solid borders (use tonal shifts)
- Use pure black text (use `on-surface` #191c1d)
- Clutter with icons (minimal, functional only)
- Use opaque borders (ghost borders at 15% max)

## File Structure

```
backend/
├── main.py           # FastAPI routes + CORS + static mount
├── orchestrator.py   # asyncio.gather() parallel pipeline
├── ingest.py         # source → Gemini → context JSON
├── context.py        # save/load context to /tmp/digest/
├── visual.py         # context → markmap markdown
├── quiz.py           # context → 10 MCQ JSON
├── cards.py          # context → 12-15 flashcard JSON
├── podcast.py        # context → script (Pro) → TTS audio (Flash TTS)
├── chat.py           # streaming text chat
└── tutor.py          # text-based Feynman Socratic tutor

frontend/
├── app/
│   ├── page.tsx      # main page (input + tabs + content)
│   ├── layout.tsx    # root layout (fonts, meta)
│   └── globals.css   # design tokens + Tailwind
└── components/
    ├── SourceInput.tsx
    ├── TabBar.tsx
    ├── Overview.tsx       # summary card + MindMap
    ├── MindMap.tsx        # markmap-view wrapper
    ├── QuizMode.tsx
    ├── FlashCards.tsx
    ├── PodcastPlayer.tsx
    ├── TutorTab.tsx       # text chat with concept dropdown
    ├── FloatingChat.tsx
    └── LoadingState.tsx
```

## API Endpoints

```
POST /api/digest          # full pipeline
POST /api/ingest          # parse + analyze → context JSON
POST /api/visual          # context → markmap markdown
POST /api/quiz            # context → 10 questions
POST /api/cards           # context → 12-15 flashcards
POST /api/podcast         # context → script + TTS WAV audio
POST /api/chat            # streaming text chat
POST /api/tutor           # text-based Socratic tutor
GET  /api/context/{sid}   # retrieve stored context
```

## Build Rounds

Each round must be independently demoable. Commit after each.

1. **Round 1:** Ingest + Overview (context.py, ingest.py, visual.py, main.py, frontend shell, Overview, MindMap)
2. **Round 2:** Quiz + Cards (quiz.py, cards.py, QuizMode.tsx, FlashCards.tsx)
3. **Round 3:** Chat + Tutor (chat.py, tutor.py, FloatingChat.tsx, TutorTab.tsx)
4. **Round 4:** Podcast (podcast.py, PodcastPlayer.tsx)

## Rules

1. **No fallback data.** All content is generated live via Gemini API.
2. **No voice/WebSocket tutor.** Tutor is text-only chat with Feynman system prompt.
3. **Tutor uses thinking.** Config: `thinking_config=types.ThinkingConfig(thinking_level="LOW")`, `temperature=1.0`
4. Add `data-*` attributes on all interactive elements for Playwright testing.
5. YouTube transcript: use `YouTubeTranscriptApi()` v2 syntax — `ytt = YouTubeTranscriptApi(); transcript = ytt.fetch(vid_id)`.
6. TTS outputs raw PCM → save as WAV (24000Hz, 16-bit mono). NOT MP3.
7. Multi-speaker TTS uses `SpeakerVoiceConfig` with speaker names "Alex"/"Sam" and voices "Kore"/"Charon".
8. Context is stored at `/tmp/digest/context_{session_id}.json`.
9. Static files (podcast audio) served from `/tmp/digest/` mounted at `/static`.
10. Do NOT refactor working code. Forward only.
11. If stuck >15 min on one issue, mock the endpoint and move on.

## Verification

Run `python tests/verify_round{N}.py` after each round. Backend must be running on :8000, frontend on :3000.

## Dependencies

```bash
# Backend (use uv)
uv add fastapi uvicorn google-genai trafilatura youtube-transcript-api httpx

# Frontend
npx create-next-app@14 frontend --typescript --tailwind --app --no-src-dir
cd frontend && npm install markmap-view markmap-lib
```

## Environment

```
GEMINI_API_KEY=xxx  # in .env, single key for all models
```
