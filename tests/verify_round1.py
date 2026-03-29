"""Verify Round 1: Ingest + Overview.

Requires: backend on :8000, frontend on :3000.
"""
import httpx
import json
import sys

BASE = "http://localhost:8000"
FRONTEND = "http://localhost:3000"

# Test URL — Anthropic engineering blog
TEST_URL = "https://www.anthropic.com/engineering/harness-design-long-running-apps"

def main():
    errors = []

    # 1. Ingest endpoint
    print("=== Testing /api/ingest ===")
    try:
        r = httpx.post(
            f"{BASE}/api/ingest",
            json={"source": TEST_URL},
            timeout=90,
        )
        assert r.status_code == 200, f"Status {r.status_code}: {r.text[:200]}"
        data = r.json()
        assert "title" in data, "Missing 'title' in context"
        assert "key_concepts" in data, "Missing 'key_concepts'"
        assert len(data["key_concepts"]) >= 5, f"Only {len(data['key_concepts'])} concepts (need >=5)"
        assert "hierarchy" in data, "Missing 'hierarchy'"
        assert "key_insights" in data, "Missing 'key_insights'"
        assert "summary" in data, "Missing 'summary'"
        print(f"  Title: {data['title']}")
        print(f"  Concepts: {len(data['key_concepts'])}")
        print(f"  Insights: {len(data['key_insights'])}")
        print("  /api/ingest PASSED")
    except Exception as e:
        errors.append(f"/api/ingest: {e}")
        print(f"  /api/ingest FAILED: {e}")
        data = None

    # 2. Visual endpoint (markmap markdown)
    print("\n=== Testing /api/visual ===")
    if data:
        try:
            r2 = httpx.post(
                f"{BASE}/api/visual",
                json=data,
                timeout=30,
            )
            assert r2.status_code == 200, f"Status {r2.status_code}"
            visual = r2.json()
            assert "markdown" in visual, "Missing 'markdown' in response"
            md = visual["markdown"]
            assert md.strip().startswith("#"), f"Markdown doesn't start with #: {md[:50]}"
            lines = [l for l in md.split("\n") if l.strip()]
            assert len(lines) >= 8, f"Only {len(lines)} lines (need >=8)"
            print(f"  Lines: {len(lines)}")
            print(f"  Preview: {md[:120]}...")
            print("  /api/visual PASSED")
        except Exception as e:
            errors.append(f"/api/visual: {e}")
            print(f"  /api/visual FAILED: {e}")
    else:
        errors.append("/api/visual: skipped (ingest failed)")
        print("  /api/visual SKIPPED (ingest failed)")

    # 3. Frontend loads
    print("\n=== Testing frontend (localhost:3000) ===")
    try:
        r3 = httpx.get(FRONTEND, timeout=10)
        assert r3.status_code == 200, f"Status {r3.status_code}"
        assert len(r3.text) > 500, "HTML response too short"
        print(f"  HTML size: {len(r3.text)} chars")
        print("  Frontend PASSED")
    except Exception as e:
        errors.append(f"Frontend: {e}")
        print(f"  Frontend FAILED: {e}")

    # 4. Context retrieval
    print("\n=== Testing /api/context ===")
    try:
        r4 = httpx.get(f"{BASE}/api/context/test", timeout=10)
        # May 404 if no test session exists yet, that's OK for round 1
        if r4.status_code == 200:
            ctx = r4.json()
            assert "title" in ctx
            print("  /api/context PASSED")
        else:
            print(f"  /api/context returned {r4.status_code} (OK if no session yet)")
    except Exception as e:
        print(f"  /api/context: {e} (non-critical)")

    # Summary
    print(f"\n{'='*50}")
    if errors:
        print(f"Round 1 FAILED ({len(errors)} errors):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("Round 1 PASSED")


if __name__ == "__main__":
    main()
