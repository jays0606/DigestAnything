"""Test → Fix → Retest Loop

The main orchestrator. Runs tests, feeds failures to a Claude agent that
fixes the code, then re-runs tests. Loops until all pass.

Usage:
    # Test all rounds + fix
    python tests/agents/loop.py

    # Test specific round
    python tests/agents/loop.py --round 2

    # E2E browser test (default: blog source)
    python tests/agents/loop.py --e2e

    # E2E with specific source type
    python tests/agents/loop.py --e2e --source youtube
    python tests/agents/loop.py --e2e --source wikipedia

    # E2E with ALL source types (blog + youtube + wikipedia)
    python tests/agents/loop.py --e2e --source all

    # Test only, no auto-fix
    python tests/agents/loop.py --no-fix

    # Restart backend/frontend between fix cycles
    python tests/agents/loop.py --restart-servers
"""

import argparse
import asyncio
import subprocess
import signal
import sys
import time
from pathlib import Path

# Add parent for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import MAX_CYCLES, PROJECT_ROOT
from test_runner import run_round, run_e2e, run_all_rounds, TestResult
from fixer import fix_failures, fix_e2e_failures
from e2e_agent import run_e2e_agent, run_full_e2e_suite, TEST_SOURCES


# ---------------------------------------------------------------------------
# Server management
# ---------------------------------------------------------------------------

_server_procs: list[subprocess.Popen] = []


def start_servers():
    """Start backend + frontend if not already running."""
    import httpx

    # Check if already running
    try:
        httpx.get("http://localhost:8000/docs", timeout=3)
        print("[servers] Backend already running on :8000")
    except Exception:
        print("[servers] Starting backend...")
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--port", "8000", "--host", "0.0.0.0"],
            cwd=str(PROJECT_ROOT / "backend"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        _server_procs.append(proc)
        time.sleep(3)

    try:
        httpx.get("http://localhost:3000", timeout=3)
        print("[servers] Frontend already running on :3000")
    except Exception:
        print("[servers] Starting frontend...")
        proc = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=str(PROJECT_ROOT / "frontend"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        _server_procs.append(proc)
        time.sleep(5)


def stop_servers():
    """Stop servers we started."""
    for proc in _server_procs:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    _server_procs.clear()


def restart_servers():
    """Kill and restart backend + frontend."""
    print("[servers] Restarting...")
    # Kill anything on ports 8000 and 3000
    subprocess.run(["lsof", "-ti:8000"], capture_output=True)  # just check
    subprocess.run(["kill", "-9", "$(lsof -ti:8000)"], shell=True, capture_output=True)
    subprocess.run(["kill", "-9", "$(lsof -ti:3000)"], shell=True, capture_output=True)
    time.sleep(2)
    stop_servers()
    start_servers()


# ---------------------------------------------------------------------------
# The Loop
# ---------------------------------------------------------------------------

async def test_fix_loop(
    round_num: int | None = None,
    e2e: bool = False,
    e2e_source: str = "blog",
    auto_fix: bool = True,
    max_cycles: int = MAX_CYCLES,
    restart: bool = False,
):
    """Main test-fix-retest loop.

    Args:
        round_num: Specific round to test (None = all rounds)
        e2e: Run browser-based E2E test
        e2e_source: Source type for E2E test ("blog", "youtube", "wikipedia", "all")
        auto_fix: Whether to auto-fix failures
        max_cycles: Max fix-retest cycles
        restart: Restart servers between fix cycles
    """
    cycle = 0

    print(f"\n{'='*60}")
    print(f"DigestAnything — Agent Test Loop")
    print(f"{'='*60}")
    if e2e:
        if e2e_source == "all":
            print(f"Mode: E2E browser (ALL sources: {', '.join(TEST_SOURCES.keys())})")
        else:
            print(f"Mode: E2E browser ({e2e_source}: {TEST_SOURCES[e2e_source]['url']})")
    elif round_num:
        print(f"Mode: Round {round_num}")
    else:
        print(f"Mode: All rounds")
    print(f"Auto-fix: {auto_fix}")
    print(f"Max cycles: {max_cycles}")
    print(f"Model: claude-opus-4-6")
    print(f"Permissions: bypass (fully autonomous)")
    print(f"{'='*60}\n")

    while cycle < max_cycles:
        cycle += 1
        print(f"\n{'#'*60}")
        print(f"# CYCLE {cycle}/{max_cycles}")
        print(f"{'#'*60}")

        # --- Step 1: Run tests ---
        if e2e:
            if e2e_source == "all":
                print("\n[test] Running E2E suite across ALL source types...")
                e2e_results = await run_full_e2e_suite()
                failing = [r for r in e2e_results if not r.passed]
                if not failing:
                    print("\n ALL E2E TESTS PASSED (blog + youtube + wikipedia)!")
                    return
                result = failing[0]  # Fix first failure
            else:
                print(f"\n[test] Running E2E agent with Playwright ({e2e_source})...")
                result = await run_e2e_agent(source_key=e2e_source)
        elif round_num:
            result = run_round(round_num)
        else:
            results = run_all_rounds()
            # Find first failing round
            failing = [r for r in results if not r.passed]
            if not failing:
                print("\n ALL ROUNDS PASSED!")
                if e2e:
                    return
                # Optionally run E2E as final check
                print("\n[bonus] Running E2E as final verification...")
                e2e_result = run_e2e()
                if e2e_result.passed:
                    print(" E2E PASSED — everything works!")
                else:
                    print(f" E2E found {len(e2e_result.errors)} issues")
                    if auto_fix:
                        result = e2e_result
                        # Fall through to fix
                    else:
                        return
                return
            result = failing[0]  # Fix one round at a time

        # --- Step 2: Check if passed ---
        if result.passed:
            label = f"Round {result.round_num}" if result.round_num else "E2E"
            print(f"\n {label} PASSED!")
            if round_num or e2e:
                return  # Done
            continue  # Move to next round

        # --- Step 3: Fix failures ---
        if not auto_fix:
            print(f"\n Tests failed. Auto-fix disabled. Stopping.")
            print(f"Errors:")
            for err in result.errors:
                print(f"  - {err}")
            return

        label = f"Round {result.round_num}" if result.round_num else "E2E"
        print(f"\n[fix] {label} failed with {len(result.errors)} errors. Sending to fixer agent...")

        if e2e or result.round_num is None:
            summary = await fix_e2e_failures(result)
        else:
            summary = await fix_failures(result)

        # --- Step 4: Optionally restart servers ---
        if restart:
            restart_servers()

        print(f"\n[loop] Fix applied. Re-testing in cycle {cycle + 1}...")
        time.sleep(2)  # Brief pause for any file watchers to pick up changes

    print(f"\n{'='*60}")
    print(f"Loop finished after {cycle} cycles")
    print(f"{'='*60}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="DigestAnything agent test-fix loop")
    parser.add_argument("--round", type=int, choices=[1, 2, 3, 4], help="Test specific round")
    parser.add_argument("--e2e", action="store_true", help="Run browser E2E test")
    parser.add_argument("--source", type=str, default="blog", choices=["blog", "youtube", "wikipedia", "all"],
                        help="Source type for E2E test (default: blog)")
    parser.add_argument("--no-fix", action="store_true", help="Test only, no auto-fix")
    parser.add_argument("--max-cycles", type=int, default=MAX_CYCLES, help=f"Max fix cycles (default: {MAX_CYCLES})")
    parser.add_argument("--restart-servers", action="store_true", help="Restart backend/frontend between cycles")
    parser.add_argument("--start-servers", action="store_true", help="Auto-start backend + frontend")
    args = parser.parse_args()

    # Handle cleanup on exit
    def cleanup(sig=None, frame=None):
        stop_servers()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        if args.start_servers:
            start_servers()

        asyncio.run(
            test_fix_loop(
                round_num=args.round,
                e2e=args.e2e,
                e2e_source=args.source,
                auto_fix=not args.no_fix,
                max_cycles=args.max_cycles,
                restart=args.restart_servers,
            )
        )
    finally:
        stop_servers()


if __name__ == "__main__":
    main()
