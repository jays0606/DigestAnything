# DigestAnything — Ralphthon Seoul #2 Presentation

## Slide 1: Title
- **Project:** DigestAnything
- **Tagline:** Any source → See it. Test it. Prove it.
- **Team:** Jaeho Shin (solo)
- **GitHub:** https://github.com/jays0606/DigestAnything

## Slide 2: Problem
- **Who:** Students, developers, professionals who consume tons of content (articles, videos, papers)
- **Problem:** Reading/watching is passive. You feel like you learned, but you can't explain it. 80% is forgotten in 24 hours (Ebbinghaus curve).
- **Frequency:** Every day — every article, every YouTube video, every PDF
- **Pain:** Hours spent consuming → almost nothing retained. No active recall, no testing, no reinforcement.
- **Story:** "I watched a 1-hour Karpathy lecture. Next day, I couldn't explain a single concept to a colleague."

## Slide 3: Solution
- **One sentence:** Paste any URL, YouTube link, or PDF → get 5 AI-powered learning experiences that make knowledge stick.
- **The 5 tabs:**
  - 🧠 Overview — summary + interactive mindmap (Dual Coding)
  - ❓ Quiz — 10 MCQs with explanations (Active Recall)
  - 🃏 Cards — 12-15 flip flashcards (Spaced Repetition)
  - 🎙️ Podcast — 2-host AI podcast (Elaborative Interrogation)
  - 🎓 Tutor — Socratic Feynman tutor (Desirable Difficulty)
  - 💬 Floating chat — ask anything about the source
- **Every tab is backed by learning science — not just AI gimmicks**

## Slide 4: Architecture & Tech
- **Stack:** Next.js + FastAPI + Gemini 3 Flash + TTS
- **Key insight:** One ingest → parallel generation of all 5 outputs via asyncio.gather()
- **Design:** Google Stitch "Cognitive Sanctuary" — warm, premium, NOT generic AI
- **Pipeline:** Source → Gemini analysis → context.json → 4 generators in parallel

## Slide 5: Ralph Setup — The Agent Loop
- **The secret sauce: Self-healing test loop**
- Claude Code autopilot builds the app (4 rounds)
- Claude Agent SDK (Opus 4.6) runs verification:
  - API tests per round (verify_round{1-4}.py)
  - Playwright E2E browser test (tests actual UI interactions)
  - Gemini audio understanding (validates podcast quality)
- **If anything fails → Opus agent reads error + code → fixes → retests**
- Tests → Fix → Retest → Repeat until perfect
- **Built the spec, tests, and agent loop BEFORE writing any code**

## Slide 6: Demo
- Live demo: paste an Anthropic blog URL
- Watch Overview load immediately, other tabs fill in
- Click through: mindmap, quiz, flashcards, podcast, tutor
- Show the floating chat
