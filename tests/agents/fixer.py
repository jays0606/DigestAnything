"""Agent that diagnoses test failures and fixes code."""

from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage
from config import (
    PROJECT_ROOT,
    MODEL,
    PERMISSION_MODE,
    MAX_TURNS_FIXER,
    FIXER_SYSTEM_PROMPT,
)
from test_runner import TestResult


async def fix_failures(result: TestResult) -> str:
    """Run a Claude agent to diagnose and fix test failures.

    Returns the agent's summary of what it fixed.
    """
    round_label = f"Round {result.round_num}" if result.round_num else "E2E"

    prompt = f"""## Test Failure Report — {round_label}

### Test Output
```
{result.output[-3000:]}
```

### Errors
{chr(10).join(f'- {e}' for e in result.errors)}

## Your Task

1. Read the test output above. Identify every distinct failure.
2. For each failure:
   a. Read the relevant source file(s) in backend/ or frontend/
   b. Identify the root cause
   c. Fix it with a minimal, targeted edit
3. After all fixes, summarize what you changed.

Do NOT:
- Modify test files (tests/)
- Add mock/fake data
- Refactor unrelated code
- Add unnecessary dependencies
"""

    summary = ""
    async for msg in query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            cwd=str(PROJECT_ROOT),
            allowed_tools=["Read", "Edit", "Write", "Glob", "Grep", "Bash"],
            permission_mode=PERMISSION_MODE,
            system_prompt=FIXER_SYSTEM_PROMPT,
            model=MODEL,
            max_turns=MAX_TURNS_FIXER,
            setting_sources=["project"],
        ),
    ):
        if isinstance(msg, ResultMessage):
            summary = msg.result
            print(f"\n[Fixer] {summary[:500]}")

    return summary


async def fix_e2e_failures(result: TestResult) -> str:
    """Fix failures found during E2E browser testing.

    Same as fix_failures but with browser context.
    """
    prompt = f"""## E2E Browser Test Failures

### Test Output
```
{result.output[-3000:]}
```

### Errors
{chr(10).join(f'- {e}' for e in result.errors)}

## Your Task

These failures were found by a Playwright browser test navigating the actual UI.
The issues could be:
- Frontend rendering bugs (React/Next.js components)
- API response format mismatches
- Missing data-* attributes for test selectors
- CSS/layout issues preventing interaction
- Backend returning unexpected data shapes

1. Read the error output. Identify what the browser couldn't find or interact with.
2. Read the relevant frontend component(s) and/or backend endpoint(s).
3. Fix each issue.
4. Summarize changes.
"""

    summary = ""
    async for msg in query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            cwd=str(PROJECT_ROOT),
            allowed_tools=["Read", "Edit", "Write", "Glob", "Grep", "Bash"],
            permission_mode="acceptEdits",
            system_prompt=FIXER_SYSTEM_PROMPT,
            model=MODEL,
            max_turns=MAX_TURNS_FIXER,
            setting_sources=["project"],
        ),
    ):
        if isinstance(msg, ResultMessage):
            summary = msg.result
            print(f"\n[Fixer] {summary[:500]}")

    return summary
