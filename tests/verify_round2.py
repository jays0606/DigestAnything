"""Verify Round 2: Quiz + Cards.

Requires: backend on :8000 with Round 1 working.

Tests:
  Quiz API:
    - POST /api/quiz → 10 questions
    - Each: id, difficulty (easy/medium/hard/expert), question, options (4), correct (0-3), explanation
    - Difficulty distribution: easy(3), medium(4), hard(2), expert(1)
    - At least 1 scenario question, 1 relationship question
  Cards API:
    - POST /api/cards → 12-15 cards
    - Each: front (1-6 words), back (2-3 sentences), type (definition/comparison/application)
    - Type distribution: definition(6-8), comparison(2-3), application(2-3)
    - Order: foundational → advanced
"""
import httpx
import json
import sys

BASE = "http://localhost:8000"
TEST_URL = "https://www.anthropic.com/engineering/harness-design-long-running-apps"


def get_context():
    print("=== Setup: Ingest ===")
    r = httpx.post(f"{BASE}/api/ingest", json={"source": TEST_URL}, timeout=90)
    assert r.status_code == 200, f"Ingest failed: {r.status_code}"
    ctx = r.json()
    print(f"  Context: {ctx['title']}")
    return ctx


def test_quiz(ctx):
    print("\n=== 1. POST /api/quiz ===")
    r = httpx.post(f"{BASE}/api/quiz", json=ctx, timeout=60)
    assert r.status_code == 200, f"Status {r.status_code}: {r.text[:300]}"
    quiz = r.json()

    assert "questions" in quiz, "Missing 'questions'"
    qs = quiz["questions"]
    assert len(qs) >= 5, f"Only {len(qs)} questions (need >=5)"

    difficulties = []
    for i, q in enumerate(qs):
        assert "id" in q, f"Q{i+1} missing 'id'"
        assert "difficulty" in q, f"Q{i+1} missing 'difficulty'"
        assert q["difficulty"] in ("easy", "medium", "hard", "expert"), f"Q{i+1} invalid difficulty: {q['difficulty']}"
        difficulties.append(q["difficulty"])
        assert "question" in q, f"Q{i+1} missing 'question'"
        assert len(q["question"]) > 20, f"Q{i+1} question too short"
        assert "options" in q, f"Q{i+1} missing 'options'"
        assert len(q["options"]) == 4, f"Q{i+1} has {len(q['options'])} options (need 4)"
        for j, opt in enumerate(q["options"]):
            assert len(opt) > 5, f"Q{i+1} option {j} too short: '{opt}'"
        assert "correct" in q, f"Q{i+1} missing 'correct'"
        assert isinstance(q["correct"], int), f"Q{i+1} 'correct' not int: {type(q['correct'])}"
        assert 0 <= q["correct"] <= 3, f"Q{i+1} 'correct' out of range: {q['correct']}"
        assert "explanation" in q, f"Q{i+1} missing 'explanation'"
        assert len(q["explanation"]) > 30, f"Q{i+1} explanation too short"

    # Difficulty distribution
    easy = difficulties.count("easy")
    medium = difficulties.count("medium")
    hard = difficulties.count("hard") + difficulties.count("expert")
    print(f"  Questions: {len(qs)} (easy={easy}, medium={medium}, hard+expert={hard})")
    assert easy >= 1, "Need at least 1 easy question"
    assert medium >= 1, "Need at least 1 medium question"

    for q in qs[:3]:
        print(f"    [{q['difficulty']}] {q['question'][:70]}...")
    print("  PASSED")


def test_cards(ctx):
    print("\n=== 2. POST /api/cards ===")
    r = httpx.post(f"{BASE}/api/cards", json=ctx, timeout=60)
    assert r.status_code == 200, f"Status {r.status_code}: {r.text[:300]}"
    cards = r.json()

    assert "cards" in cards, "Missing 'cards'"
    cs = cards["cards"]
    assert len(cs) >= 8, f"Only {len(cs)} cards (need >=8)"

    types = []
    for i, c in enumerate(cs):
        assert "front" in c, f"Card {i+1} missing 'front'"
        assert "back" in c, f"Card {i+1} missing 'back'"
        assert "type" in c, f"Card {i+1} missing 'type'"
        assert c["type"] in ("definition", "comparison", "application"), f"Card {i+1} invalid type: {c['type']}"
        types.append(c["type"])
        # Front should be concise
        assert len(c["front"]) <= 80, f"Card {i+1} front too long ({len(c['front'])} chars)"
        # Back should be substantive
        assert len(c["back"]) > 20, f"Card {i+1} back too short ({len(c['back'])} chars)"

    defs = types.count("definition")
    comps = types.count("comparison")
    apps = types.count("application")
    print(f"  Cards: {len(cs)} (definition={defs}, comparison={comps}, application={apps})")
    assert defs >= 3, f"Need >=3 definition cards (got {defs})"

    for c in cs[:3]:
        print(f"    [{c['type']}] {c['front']} → {c['back'][:50]}...")
    print("  PASSED")


def main():
    errors = []
    ctx = get_context()

    for name, fn in [("quiz", lambda: test_quiz(ctx)), ("cards", lambda: test_cards(ctx))]:
        try:
            fn()
        except Exception as e:
            errors.append(f"{name}: {e}")
            print(f"  FAILED: {e}")

    print(f"\n{'='*60}")
    if errors:
        print(f"Round 2 FAILED ({len(errors)} errors):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("Round 2 PASSED — Quiz + Cards all working")


if __name__ == "__main__":
    main()
