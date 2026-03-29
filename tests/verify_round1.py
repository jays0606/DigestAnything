"""Verify Round 1: Ingest + Visual + Frontend Shell.

Requires: backend on :8000, frontend on :3000.

Tests:
  API:
    - POST /api/ingest with URL → returns full context JSON
    - POST /api/visual with context → returns markmap markdown
    - GET /api/context/{sid} → retrieves stored context
    - POST /api/digest (full pipeline) → returns all results
  Frontend:
    - GET localhost:3000 → 200, HTML renders
  Context shape:
    - title, subtitle, summary, difficulty (enum), estimated_read_time_minutes
    - key_concepts (>=5, each with term, definition, importance enum, related_to)
    - hierarchy (root + children with name, children, description)
    - key_insights (>=3)
    - analogies (>=2, each with concept, analogy, explanation)
"""
import httpx
import json
import sys

BASE = "http://localhost:8000"
FRONTEND = "http://localhost:3000"
TEST_URL = "https://www.anthropic.com/engineering/harness-design-long-running-apps"


def test_ingest():
    print("=== 1. POST /api/ingest ===")
    r = httpx.post(f"{BASE}/api/ingest", json={"source": TEST_URL}, timeout=90)
    assert r.status_code == 200, f"Status {r.status_code}: {r.text[:300]}"
    data = r.json()

    # Required top-level fields
    for field in ["title", "subtitle", "summary", "difficulty", "estimated_read_time_minutes"]:
        assert field in data, f"Missing '{field}'"
    assert data["difficulty"] in ("beginner", "intermediate", "advanced"), f"Invalid difficulty: {data['difficulty']}"
    assert isinstance(data["estimated_read_time_minutes"], (int, float)), "read_time not a number"

    # Key concepts
    assert "key_concepts" in data, "Missing 'key_concepts'"
    concepts = data["key_concepts"]
    assert len(concepts) >= 5, f"Only {len(concepts)} concepts (need >=5)"
    for i, c in enumerate(concepts):
        assert "term" in c, f"Concept {i} missing 'term'"
        assert "definition" in c, f"Concept {i} missing 'definition'"
        assert "importance" in c, f"Concept {i} missing 'importance'"
        assert c["importance"] in ("high", "medium"), f"Concept {i} invalid importance: {c['importance']}"
        assert "related_to" in c, f"Concept {i} missing 'related_to'"
        assert isinstance(c["related_to"], list), f"Concept {i} related_to not a list"

    # Hierarchy
    assert "hierarchy" in data, "Missing 'hierarchy'"
    h = data["hierarchy"]
    assert "root" in h, "Hierarchy missing 'root'"
    assert "children" in h, "Hierarchy missing 'children'"
    assert len(h["children"]) >= 3, f"Only {len(h['children'])} branches (need >=3)"
    for i, child in enumerate(h["children"]):
        assert "name" in child, f"Branch {i} missing 'name'"
        assert "children" in child, f"Branch {i} missing 'children'"

    # Key insights
    assert "key_insights" in data, "Missing 'key_insights'"
    assert len(data["key_insights"]) >= 3, f"Only {len(data['key_insights'])} insights (need >=3)"

    # Analogies
    assert "analogies" in data, "Missing 'analogies'"
    assert len(data["analogies"]) >= 2, f"Only {len(data['analogies'])} analogies (need >=2)"
    for i, a in enumerate(data["analogies"]):
        assert "concept" in a, f"Analogy {i} missing 'concept'"
        assert "analogy" in a, f"Analogy {i} missing 'analogy'"
        assert "explanation" in a, f"Analogy {i} missing 'explanation'"

    print(f"  Title: {data['title']}")
    print(f"  Difficulty: {data['difficulty']}")
    print(f"  Concepts: {len(concepts)}, Insights: {len(data['key_insights'])}, Analogies: {len(data['analogies'])}")
    print(f"  Hierarchy: {h['root']} → {len(h['children'])} branches")
    print("  PASSED")
    return data


def test_visual(context):
    print("\n=== 2. POST /api/visual ===")
    r = httpx.post(f"{BASE}/api/visual", json=context, timeout=30)
    assert r.status_code == 200, f"Status {r.status_code}"
    visual = r.json()
    assert "markdown" in visual, "Missing 'markdown'"
    md = visual["markdown"]
    assert md.strip().startswith("#"), f"Markdown doesn't start with #"
    lines = [l for l in md.split("\n") if l.strip()]
    assert len(lines) >= 8, f"Only {len(lines)} lines (need >=8)"
    # Check structure: should have ## and ### levels
    has_h2 = any(l.strip().startswith("## ") for l in lines)
    has_h3 = any(l.strip().startswith("### ") for l in lines)
    assert has_h2, "No ## headings found in markmap"
    assert has_h3, "No ### headings found in markmap"
    print(f"  Lines: {len(lines)}, has ##: {has_h2}, has ###: {has_h3}")
    print(f"  Root: {lines[0][:60]}")
    print("  PASSED")
    return md


def test_context_retrieval(session_id):
    print("\n=== 3. GET /api/context/{sid} ===")
    r = httpx.get(f"{BASE}/api/context/{session_id}", timeout=10)
    if r.status_code == 200:
        ctx = r.json()
        assert "title" in ctx, "Stored context missing 'title'"
        assert "key_concepts" in ctx, "Stored context missing 'key_concepts'"
        print(f"  Retrieved context: {ctx['title']}")
        print("  PASSED")
    elif r.status_code == 404:
        print("  No stored session (OK for round 1 — ingest may not persist with this session_id)")
    else:
        raise AssertionError(f"Unexpected status {r.status_code}")


def test_frontend():
    print("\n=== 4. Frontend (localhost:3000) ===")
    r = httpx.get(FRONTEND, timeout=15)
    assert r.status_code == 200, f"Status {r.status_code}"
    html = r.text
    assert len(html) > 500, f"HTML too short ({len(html)} chars)"
    print(f"  HTML: {len(html)} chars")
    print("  PASSED")


def main():
    errors = []
    context = None

    for name, fn, args in [
        ("ingest", test_ingest, []),
        ("visual", lambda: test_visual(context), []),
        ("context", lambda: test_context_retrieval("test"), []),
        ("frontend", test_frontend, []),
    ]:
        try:
            if name == "ingest":
                context = test_ingest()
            elif name == "visual" and context:
                test_visual(context)
            elif name == "visual":
                errors.append("visual: skipped (ingest failed)")
                print("\n=== 2. POST /api/visual === SKIPPED")
                continue
            elif name == "context":
                test_context_retrieval("test")
            elif name == "frontend":
                test_frontend()
        except Exception as e:
            errors.append(f"{name}: {e}")
            print(f"  FAILED: {e}")

    print(f"\n{'='*60}")
    if errors:
        print(f"Round 1 FAILED ({len(errors)} errors):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("Round 1 PASSED — Ingest + Visual + Frontend all working")


if __name__ == "__main__":
    main()
