"""Run existing verify_round*.py scripts and capture results."""

import subprocess
import sys
from dataclasses import dataclass
from config import TESTS_DIR, ROUND_SCRIPTS, E2E_SCRIPT


@dataclass
class TestResult:
    round_num: int | None  # None for E2E
    passed: bool
    output: str
    errors: list[str]


def run_test_script(script_name: str, round_num: int | None = None) -> TestResult:
    """Run a test script and capture output."""
    script_path = TESTS_DIR / script_name

    if not script_path.exists():
        return TestResult(
            round_num=round_num,
            passed=False,
            output=f"Script not found: {script_path}",
            errors=[f"Missing test script: {script_name}"],
        )

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=180,  # 3 min timeout (Gemini API calls take time)
            cwd=str(TESTS_DIR),
        )

        output = result.stdout + result.stderr
        passed = result.returncode == 0

        # Extract error lines
        errors = []
        for line in output.split("\n"):
            line_stripped = line.strip()
            if "FAILED" in line_stripped or "Error" in line_stripped or "AssertionError" in line_stripped:
                errors.append(line_stripped)

        return TestResult(
            round_num=round_num,
            passed=passed,
            output=output,
            errors=errors,
        )

    except subprocess.TimeoutExpired:
        return TestResult(
            round_num=round_num,
            passed=False,
            output="Test script timed out after 180s",
            errors=["Timeout — backend may be down or Gemini API unresponsive"],
        )
    except Exception as e:
        return TestResult(
            round_num=round_num,
            passed=False,
            output=str(e),
            errors=[str(e)],
        )


def run_round(round_num: int) -> TestResult:
    """Run verification for a specific round."""
    script = ROUND_SCRIPTS.get(round_num)
    if not script:
        return TestResult(
            round_num=round_num,
            passed=False,
            output=f"No script for round {round_num}",
            errors=[f"Unknown round: {round_num}"],
        )
    print(f"\n{'='*60}")
    print(f"Running Round {round_num}: {script}")
    print(f"{'='*60}")
    return run_test_script(script, round_num)


def run_e2e() -> TestResult:
    """Run the full E2E browser test."""
    print(f"\n{'='*60}")
    print(f"Running E2E: {E2E_SCRIPT}")
    print(f"{'='*60}")
    return run_test_script(E2E_SCRIPT, round_num=None)


def run_all_rounds() -> list[TestResult]:
    """Run all round verification scripts."""
    results = []
    for round_num in sorted(ROUND_SCRIPTS.keys()):
        result = run_round(round_num)
        results.append(result)
        status = "PASS" if result.passed else "FAIL"
        print(f"\nRound {round_num}: {status}")
        if not result.passed:
            for err in result.errors[:5]:
                print(f"  - {err}")
    return results
