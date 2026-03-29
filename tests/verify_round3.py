"""Verify Round 3: Chat + Tutor.

Requires: backend on :8000 with /api/ingest working (Round 1 complete).
"""
import httpx
import json
import sys

BASE = "http://localhost:8000"
TEST_URL = "https://www.anthropic.com/engineering/harness-design-long-running-apps"


def setup_session():
    """Ingest content to create a session for chat/tutor."""
    print("=== Setting up session (ingest) ===")
    r = httpx.post(f"{BASE}/api/ingest", json={"source": TEST_URL}, timeout=90)
    assert r.status_code == 200, f"Ingest failed: {r.status_code}"
    ctx = r.json()
    # Use a known session ID for testing
    session_id = ctx.get("session_id", "test")
    print(f"  Session: {session_id}, Title: {ctx['title']}")
    return session_id, ctx


def main():
    errors = []
    session_id, ctx = setup_session()

    # 1. Chat endpoint
    print("\n=== Testing /api/chat ===")
    try:
        r = httpx.post(
            f"{BASE}/api/chat",
            json={
                "message": "What is this content about? Summarize in 2 sentences.",
                "session_id": session_id,
            },
            timeout=30,
        )
        assert r.status_code == 200, f"Status {r.status_code}: {r.text[:200]}"
        # Chat may return JSON or plain text depending on streaming
        text = r.text
        assert len(text) > 30, f"Response too short ({len(text)} chars): {text}"
        print(f"  Response ({len(text)} chars): {text[:150]}...")
        print("  /api/chat PASSED")
    except Exception as e:
        errors.append(f"/api/chat: {e}")
        print(f"  /api/chat FAILED: {e}")

    # 2. Tutor endpoint
    print("\n=== Testing /api/tutor ===")
    try:
        # First message — tutor should prompt student to explain
        r = httpx.post(
            f"{BASE}/api/tutor",
            json={
                "message": "Can you help me understand the main concept?",
                "session_id": session_id,
            },
            timeout=30,
        )
        assert r.status_code == 200, f"Status {r.status_code}: {r.text[:200]}"
        tutor_data = r.json()
        assert "response" in tutor_data, "Missing 'response' in tutor output"
        resp = tutor_data["response"]
        assert len(resp) > 20, f"Tutor response too short ({len(resp)} chars)"
        print(f"  Response ({len(resp)} chars): {resp[:150]}...")
        print("  /api/tutor PASSED")
    except Exception as e:
        errors.append(f"/api/tutor: {e}")
        print(f"  /api/tutor FAILED: {e}")

    # 3. Tutor with concept selection
    print("\n=== Testing /api/tutor (with concept) ===")
    try:
        concept = ctx["key_concepts"][0]["term"] if ctx.get("key_concepts") else "main topic"
        r = httpx.post(
            f"{BASE}/api/tutor",
            json={
                "message": f"I think {concept} means something about how the system works...",
                "session_id": session_id,
                "concept": concept,
            },
            timeout=30,
        )
        assert r.status_code == 200, f"Status {r.status_code}"
        tutor_data = r.json()
        assert "response" in tutor_data
        resp = tutor_data["response"]
        assert len(resp) > 20, f"Too short: {len(resp)} chars"
        print(f"  Concept: {concept}")
        print(f"  Response: {resp[:150]}...")
        print("  /api/tutor (concept) PASSED")
    except Exception as e:
        errors.append(f"/api/tutor (concept): {e}")
        print(f"  /api/tutor (concept) FAILED: {e}")

    # Summary
    print(f"\n{'='*50}")
    if errors:
        print(f"Round 3 FAILED ({len(errors)} errors):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("Round 3 PASSED")


if __name__ == "__main__":
    main()
