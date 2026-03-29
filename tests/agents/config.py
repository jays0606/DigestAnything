"""Shared config for agent-powered testing."""

import os
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
TESTS_DIR = PROJECT_ROOT / "tests"

# URLs
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
TEST_SOURCE_URL = "https://www.anthropic.com/engineering/harness-design-long-running-apps"

# Agent SDK config
MODEL = "claude-opus-4-6"  # Opus 4.6 — 1M context via CLI config
PERMISSION_MODE = "bypassPermissions"  # fully autonomous — no prompts
MAX_CYCLES = 5              # max test-fix-retest loops
MAX_TURNS_FIXER = 60        # max agent turns per fix cycle
MAX_TURNS_E2E = 80          # max agent turns for E2E

# Round → test script mapping
ROUND_SCRIPTS = {
    1: "verify_round1.py",
    2: "verify_round2.py",
    3: "verify_round3.py",
    4: "verify_round4.py",
}
E2E_SCRIPT = "verify_e2e.py"
AUDIO_SCRIPT = "verify_audio.py"

# System prompts
FIXER_SYSTEM_PROMPT = f"""You are a senior developer fixing bugs in DigestAnything.

Project: Learning platform — paste URL → get 5 AI-powered tabs (Overview, Quiz, Cards, Podcast, Tutor).
Stack: FastAPI backend (port 8000), Next.js 14 frontend (port 3000).
Backend: Python with google-genai (Gemini API).
Frontend: TypeScript + Tailwind CSS.

Project root: {PROJECT_ROOT}
Backend dir: {BACKEND_DIR}
Frontend dir: {FRONTEND_DIR}

Rules:
1. Read the failing test output carefully. Identify the EXACT error.
2. Read the relevant source file(s) before making any change.
3. Make minimal, targeted fixes. Do NOT refactor working code.
4. After fixing, explain what you changed and why.
5. If a fix requires restarting the server, say so.
6. Do NOT mock data. All content must come from Gemini API.
7. Do NOT add new dependencies without explaining why.
"""

E2E_SYSTEM_PROMPT = f"""You are a QA engineer testing DigestAnything in a real browser.

Project: Learning platform — paste URL → get 5 AI-powered tabs.
Frontend: http://localhost:3000
Backend: http://localhost:8000

Test source URL: {TEST_SOURCE_URL}

Your job:
1. Navigate to the frontend
2. Submit the test URL
3. Wait for content to load (Gemini API can take 30-60s)
4. Verify each tab: Overview (summary + mindmap), Quiz (10 MCQs), Cards (12+ flashcards), Podcast (audio player), Tutor (Socratic chat)
5. Test interactivity: click quiz answers, flip cards, send chat messages
6. Take screenshots as evidence
7. Report PASS/FAIL per feature with details
"""
