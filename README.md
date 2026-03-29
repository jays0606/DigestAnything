# DIGEST

> Any source → See it. Test it. Prove it.

Paste any URL, YouTube link, or PDF. Get 5 AI-powered learning experiences + a chatbot.

Built at **Ralphthon Seoul #2** (March 29, 2026).

## Features

| Tab | What | Learning Science |
|-----|------|-----------------|
| Overview | Summary + interactive mindmap | Dual Coding |
| Quiz | 10 multiple-choice questions | Active Recall |
| Cards | 12-15 flip flashcards | Spaced Repetition |
| Podcast | 15min two-host AI podcast | Elaborative Interrogation |
| Tutor | Socratic text tutor | Feynman Technique |
| Chat | Floating Q&A chatbot | On-demand reinforcement |

## Stack

- **Frontend:** Next.js 14 + Tailwind CSS
- **Backend:** FastAPI (Python, async)
- **AI:** Gemini 3 Flash / Pro / TTS
- **Design:** Google Stitch ("Cognitive Sanctuary")
- **Diagrams:** Markmap

## Setup

```bash
# Backend
uv sync
cp .env.example .env  # add your GEMINI_API_KEY
uv run uvicorn backend.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

## Environment

```
GEMINI_API_KEY=your_key_here
```

## Architecture

```
Source (URL / YouTube / PDF)
       │
       ▼
  Gemini 3 Flash — parse + structured analysis
       │
       ▼
  context_{session}.json
       │
  asyncio.gather() — ALL PARALLEL:
  │         │        │         │
  ▼         ▼        ▼         ▼
Visual    Quiz     Cards    Podcast
(Flash)  (Flash)  (Flash)  (Pro+TTS)

Chat + Tutor read context on demand
```

## License

MIT
