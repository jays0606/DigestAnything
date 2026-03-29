"""Run all Gemini API tests sequentially."""
import subprocess, sys, os, time

TESTS = [
    "test_00_setup.py",
    "test_01_flash_text.py",
    "test_02_pro_text.py",
    "test_03_pdf_upload.py",
    "test_04_tts_single.py",
    "test_05_tts_multi.py",
    "test_06_youtube.py",
    "test_07_web_content.py",
    "test_08_video_understanding.py",
    "test_09_full_pipeline.py",
]

test_dir = os.path.dirname(os.path.abspath(__file__))
passed, failed, skipped = [], [], []

for test in TESTS:
    path = os.path.join(test_dir, test)
    print(f"\n{'='*60}")
    print(f"Running {test}...")
    print(f"{'='*60}")
    start = time.time()
    try:
        result = subprocess.run(
            [sys.executable, path],
            capture_output=True,
            text=True,
            timeout=120,
            env={**os.environ},
        )
        elapsed = time.time() - start
        print(result.stdout)
        if result.returncode == 0:
            passed.append((test, elapsed))
            print(f"  -> PASSED ({elapsed:.1f}s)")
        else:
            failed.append((test, result.stderr[:300]))
            print(f"  -> FAILED ({elapsed:.1f}s)")
            print(f"  stderr: {result.stderr[:300]}")
    except subprocess.TimeoutExpired:
        failed.append((test, "TIMEOUT"))
        print(f"  -> TIMEOUT (>120s)")
    except Exception as e:
        failed.append((test, str(e)))
        print(f"  -> ERROR: {e}")

print(f"\n{'='*60}")
print(f"RESULTS: {len(passed)} passed, {len(failed)} failed")
print(f"{'='*60}")
for t, elapsed in passed:
    print(f"  PASS  {t} ({elapsed:.1f}s)")
for t, err in failed:
    print(f"  FAIL  {t}: {err[:80]}")
