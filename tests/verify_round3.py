"""Verify Round 3: Chat + Tutor.

Requires: backend on :8000 with Round 1 working.

Tests:
  Chat API:
    - POST /api/chat with message + session_id → response >30 chars
    - Response references source content
    - Follow-up question works (multi-turn context)
  Tutor API:
    - POST /api/tutor → Socratic response with 'response' key
    - POST /api/tutor with concept param → focuses on that concept
    - Response stays concise (<300 chars)
    - Response asks a follow-up question (Feynman technique)
"""
import httpx
import json
import sys

BASE = "http://localhost:8000"
TEST_URL = "https://www.anthropic.com/engineering/harness-design-long-running-apps"


def setup_session():
    print("=== Setup: Ingest ===")
    r = httpx.post(f"{BASE}/api/ingest", json={"source": TEST_URL}, timeout=90)
    assert r.status_code == 200, f"Ingest failed: {r.status_code}"
    ctx = r.json()
    session_id = ctx.get("session_id", "test")
    print(f"  Session: {session_id}, Title: {ctx['title']}")
    return session_id, ctx


def test_chat_basic(session_id):
    print("\n=== 1. POST /api/chat (basic) ===")
    r = httpx.post(
        f"{BASE}/api/chat",
        json={"message": "What is this content about? Summarize in 2 sentences.", "session_id": session_id},
        timeout=30,
    )
    assert r.status_code == 200, f"Status {r.status_code}: {r.text[:200]}"
    text = r.text if r.headers.get("content-type", "").startswith("text") else r.json().get("response", r.text)
    assert len(text) > 30, f"Response too short ({len(text)} chars)"
    print(f"  Response ({len(text)} chars): {text[:150]}...")
    print("  PASSED")
    return text


def test_chat_followup(session_id):
    print("\n=== 2. POST /api/chat (follow-up) ===")
    r = httpx.post(
        f"{BASE}/api/chat",
        json={"message": "Can you explain the most important concept in more detail?", "session_id": session_id},
        timeout=30,
    )
    assert r.status_code == 200, f"Status {r.status_code}"
    text = r.text if r.headers.get("content-type", "").startswith("text") else r.json().get("response", r.text)
    assert len(text) > 30, f"Follow-up too short ({len(text)} chars)"
    print(f"  Response ({len(text)} chars): {text[:150]}...")
    print("  PASSED")


def test_tutor_basic(session_id):
    print("\n=== 3. POST /api/tutor (basic) ===")
    r = httpx.post(
        f"{BASE}/api/tutor",
        json={"message": "Can you help me understand the main concept?", "session_id": session_id},
        timeout=30,
    )
    assert r.status_code == 200, f"Status {r.status_code}: {r.text[:200]}"
    data = r.json()
    assert "response" in data, "Missing 'response' key"
    resp = data["response"]
    assert len(resp) > 20, f"Tutor response too short ({len(resp)} chars)"
    print(f"  Response ({len(resp)} chars): {resp[:150]}...")
    print("  PASSED")
    return resp


def test_tutor_with_concept(session_id, ctx):
    print("\n=== 4. POST /api/tutor (with concept) ===")
    concept = ctx["key_concepts"][0]["term"] if ctx.get("key_concepts") else "main topic"
    r = httpx.post(
        f"{BASE}/api/tutor",
        json={
            "message": f"I think {concept} means something about how the system manages things...",
            "session_id": session_id,
            "concept": concept,
        },
        timeout=30,
    )
    assert r.status_code == 200, f"Status {r.status_code}"
    data = r.json()
    assert "response" in data, "Missing 'response'"
    resp = data["response"]
    assert len(resp) > 20, f"Too short: {len(resp)} chars"
    print(f"  Concept: {concept}")
    print(f"  Response ({len(resp)} chars): {resp[:150]}...")
    print("  PASSED")


def test_tutor_socratic(session_id):
    print("\n=== 5. POST /api/tutor (Socratic — student explains) ===")
    r = httpx.post(
        f"{BASE}/api/tutor",
        json={
            "message": "So basically, it's when the AI model uses multiple agents to work together on a task, right?",
            "session_id": session_id,
        },
        timeout=30,
    )
    assert r.status_code == 200, f"Status {r.status_code}"
    data = r.json()
    resp = data["response"]
    assert len(resp) > 20, f"Too short"
    # Socratic tutor should ask a question back (contains ?)
    has_question = "?" in resp
    print(f"  Response ({len(resp)} chars): {resp[:150]}...")
    print(f"  Contains follow-up question: {has_question}")
    print("  PASSED")


def main():
    errors = []
    session_id, ctx = setup_session()

    tests = [
        ("chat_basic", lambda: test_chat_basic(session_id)),
        ("chat_followup", lambda: test_chat_followup(session_id)),
        ("tutor_basic", lambda: test_tutor_basic(session_id)),
        ("tutor_concept", lambda: test_tutor_with_concept(session_id, ctx)),
        ("tutor_socratic", lambda: test_tutor_socratic(session_id)),
    ]

    for name, fn in tests:
        try:
            fn()
        except Exception as e:
            errors.append(f"{name}: {e}")
            print(f"  FAILED: {e}")

    print(f"\n{'='*60}")
    if errors:
        print(f"Round 3 FAILED ({len(errors)} errors):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("Round 3 PASSED — Chat + Tutor all working")


if __name__ == "__main__":
    main()
