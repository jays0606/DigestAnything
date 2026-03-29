"""Verify Round 2: Quiz + Cards.

Requires: backend on :8000 with /api/ingest working (Round 1 complete).
"""
import httpx
import json
import sys

BASE = "http://localhost:8000"
TEST_URL = "https://www.anthropic.com/engineering/harness-design-long-running-apps"


def get_context():
    """Get context by ingesting test URL."""
    print("=== Getting context (ingest) ===")
    r = httpx.post(f"{BASE}/api/ingest", json={"source": TEST_URL}, timeout=90)
    assert r.status_code == 200, f"Ingest failed: {r.status_code}"
    ctx = r.json()
    print(f"  Context: {ctx['title']}")
    return ctx


def main():
    errors = []
    ctx = get_context()

    # 1. Quiz endpoint
    print("\n=== Testing /api/quiz ===")
    try:
        r = httpx.post(f"{BASE}/api/quiz", json=ctx, timeout=60)
        assert r.status_code == 200, f"Status {r.status_code}: {r.text[:200]}"
        quiz = r.json()
        assert "questions" in quiz, "Missing 'questions'"
        qs = quiz["questions"]
        assert len(qs) >= 5, f"Only {len(qs)} questions (need >=5)"

        for i, q in enumerate(qs):
            assert "question" in q, f"Q{i+1} missing 'question'"
            assert "options" in q, f"Q{i+1} missing 'options'"
            assert len(q["options"]) == 4, f"Q{i+1} has {len(q['options'])} options (need 4)"
            assert "correct" in q, f"Q{i+1} missing 'correct'"
            assert isinstance(q["correct"], int), f"Q{i+1} 'correct' not int"
            assert 0 <= q["correct"] <= 3, f"Q{i+1} 'correct' out of range: {q['correct']}"
            assert "explanation" in q, f"Q{i+1} missing 'explanation'"

        print(f"  Questions: {len(qs)}")
        for q in qs[:3]:
            print(f"    Q: {q['question'][:70]}...")
        print("  /api/quiz PASSED")
    except Exception as e:
        errors.append(f"/api/quiz: {e}")
        print(f"  /api/quiz FAILED: {e}")

    # 2. Cards endpoint
    print("\n=== Testing /api/cards ===")
    try:
        r = httpx.post(f"{BASE}/api/cards", json=ctx, timeout=60)
        assert r.status_code == 200, f"Status {r.status_code}: {r.text[:200]}"
        cards = r.json()
        assert "cards" in cards, "Missing 'cards'"
        cs = cards["cards"]
        assert len(cs) >= 8, f"Only {len(cs)} cards (need >=8)"

        for i, c in enumerate(cs):
            assert "front" in c, f"Card {i+1} missing 'front'"
            assert "back" in c, f"Card {i+1} missing 'back'"
            assert "type" in c, f"Card {i+1} missing 'type'"
            assert c["type"] in ("definition", "comparison", "application"), (
                f"Card {i+1} invalid type: {c['type']}"
            )

        print(f"  Cards: {len(cs)}")
        for c in cs[:3]:
            print(f"    [{c['type']}] {c['front']}")
        print("  /api/cards PASSED")
    except Exception as e:
        errors.append(f"/api/cards: {e}")
        print(f"  /api/cards FAILED: {e}")

    # Summary
    print(f"\n{'='*50}")
    if errors:
        print(f"Round 2 FAILED ({len(errors)} errors):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("Round 2 PASSED")


if __name__ == "__main__":
    main()
