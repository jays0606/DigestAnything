# Agent-Powered Test & Fix Loop

Uses the Claude Agent SDK to run E2E tests, diagnose failures, fix code, and re-verify — in a loop until everything passes.

## Prerequisites

```bash
# 1. Install Claude Agent SDK
uv add --dev claude-agent-sdk

# 2. Install Playwright (for browser-based E2E)
uv add --dev playwright
uv run playwright install chromium

# 3. Set environment variables in .env
ANTHROPIC_OAUTH_TOKEN=sk-ant-oat01-...   # Claude Agent SDK auth
GEMINI_API_KEY=...                        # For the app itself
```

## Which Model Does It Use?

The Agent SDK uses **your local Claude Code CLI** under the hood. It inherits whatever model your CLI is configured with (Opus 4.6 by default). You can override per-agent:

```python
options = ClaudeAgentOptions(model="claude-opus-4-6")  # explicit
```

The 1M context window beta is available if your CLI supports it — the agent can read your entire codebase in one shot.

## How to Run

### Quick: Test everything, fix what's broken
```bash
# Start backend + frontend first
cd backend && uv run uvicorn main:app --port 8000 &
cd frontend && npm run dev &

# Run the loop (max 5 fix cycles)
uv run python tests/agents/loop.py
```

### Per-round verification
```bash
uv run python tests/agents/loop.py --round 1
uv run python tests/agents/loop.py --round 2
```

### Just test, no fixing
```bash
uv run python tests/agents/loop.py --no-fix
```

### Full E2E with browser
```bash
uv run python tests/agents/loop.py --e2e
```

## Architecture

```
loop.py              # Main test-fix-retest loop orchestrator
test_runner.py       # Runs existing verify_round*.py scripts, captures output
fixer.py             # Agent that reads failures + source code, applies fixes
e2e_agent.py         # Agent that does browser-based E2E via Playwright MCP
config.py            # Shared config (model, budget, paths)
```

### The Loop

```
┌─────────────┐
│  Run Tests  │ ← runs verify_round{N}.py or verify_e2e.py
└──────┬──────┘
       │ failures?
       ▼ yes
┌─────────────┐
│  Diagnose   │ ← agent reads error output + source code
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Fix Code   │ ← agent edits backend/ or frontend/ files
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Re-Test    │ ← same tests again
└──────┬──────┘
       │ still failing?
       ▼ loop (max N cycles)
```

## Budget Control

Default: $2/cycle, $10 total max. Override:
```bash
uv run python tests/agents/loop.py --max-budget 20 --max-cycles 10
```
