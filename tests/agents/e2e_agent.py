"""Agent-powered E2E testing via Playwright MCP.

Uses a Claude agent that navigates the browser with full knowledge of
the actual DOM selectors, test scenarios, and expected behavior.
"""

from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage
from config import (
    PROJECT_ROOT,
    MODEL,
    PERMISSION_MODE,
    MAX_TURNS_E2E,
    FRONTEND_URL,
    E2E_SYSTEM_PROMPT,
)
from test_runner import TestResult


# ---------------------------------------------------------------------------
# Test sources — different content types the app should handle
# ---------------------------------------------------------------------------

TEST_SOURCES = {
    "blog": {
        "url": "https://www.anthropic.com/engineering/harness-design-long-running-apps",
        "label": "Tech blog (web article)",
        "expect": "Content about AI agent harness design, GAN-inspired architecture",
    },
    "youtube": {
        "url": "https://www.youtube.com/watch?v=zjkBMFhNj_g",
        "label": "YouTube video (transcript-based)",
        "expect": "Content extracted from YouTube transcript",
    },
    "wikipedia": {
        "url": "https://en.wikipedia.org/wiki/Transformer_(deep_learning_architecture)",
        "label": "Wikipedia (long-form article)",
        "expect": "Content about transformer architecture, attention mechanism",
    },
}

# ---------------------------------------------------------------------------
# Exact DOM selectors (from actual frontend components)
# ---------------------------------------------------------------------------

SELECTORS = """
## Exact DOM Selectors (from the actual codebase)

### Input & Submit
- Source input: `[data-source-input]` (text input field)
- Submit button: `[data-submit]` (says "Digest" or "Digesting...")
- Preset buttons: `[data-preset="blog"]`, `[data-preset="youtube"]`

### Loading
- Loading state: `[data-loading]`

### Tab Bar
- Tab buttons: `[data-tab="overview"]`, `[data-tab="quiz"]`, `[data-tab="cards"]`, `[data-tab="podcast"]`, `[data-tab="tutor"]`

### Overview Tab
- Container: `[data-content="overview"]`
- Mindmap: `[data-mindmap]` (contains SVG after render)

### Quiz Tab
- Container: `[data-content="quiz"]`
- Answer options: `[data-option="0"]`, `[data-option="1"]`, `[data-option="2"]`, `[data-option="3"]`
- Explanation (after answer): `[data-explanation]`
- Next question button: `[data-next-question]`

### Flashcards Tab
- Container: `[data-content="cards"]`
- Card (click to flip): `[data-card]`
- Previous card: `[data-prev-card]`
- Next card: `[data-next-card]`
- "Got it" button: `[data-got-it]`
- "Review again" button: `[data-review-again]`

### Podcast Tab
- Container: `[data-content="podcast"]`
- Play button: `[data-play]`
- Toggle transcript: `[data-toggle-transcript]`
- Transcript lines: `[data-transcript-line]`

### Tutor Tab
- Container: `[data-content="tutor"]`
- Concept dropdown: `[data-concept-select]`
- Chat input: `[data-tutor-input]`
- Send button: `[data-tutor-send]`
- Messages: `[data-msg]`

### Floating Chat
- Toggle bubble: `[data-chat-toggle]`
- Chat panel: `[data-chat-panel]`
- Chat input: `[data-chat-input]`
- Send button: `[data-chat-send]`
- Messages: `[data-chat-panel] [data-msg]`

### Tab Behavior
- Tabs load lazily: clicking Quiz/Cards/Podcast triggers API fetch
- While loading: shows "Generating..." text in `[data-content="X"]` div
- When ready: component replaces the placeholder div
- Overview + visual load with initial /api/digest call
- Tutor renders immediately (no extra API call, just chat interface)
"""

# ---------------------------------------------------------------------------
# E2E test scenarios
# ---------------------------------------------------------------------------

def build_e2e_prompt(source_key: str = "blog") -> str:
    """Build the full E2E test prompt for a given source type."""
    source = TEST_SOURCES[source_key]

    return f"""## E2E Browser Test: DigestAnything

### Source Under Test
- **Type:** {source['label']}
- **URL:** {source['url']}
- **Expected:** {source['expect']}

{SELECTORS}

### Instructions

Navigate to {FRONTEND_URL} and run the following test plan.
Take a screenshot after EVERY step. Use the exact selectors above.

---

#### STEP 1: Page Load
1. Navigate to `{FRONTEND_URL}`
2. Wait for page to load
3. Verify `[data-source-input]` exists
4. Verify `[data-submit]` exists and says "Digest"
5. Screenshot: "01_initial_load"

#### STEP 2: Submit Source
1. {'Click `[data-preset="blog"]` (uses preset URL)' if source_key == 'blog' else f'Type `{source["url"]}` into `[data-source-input]`'}
{'2. (Preset auto-submits)' if source_key == 'blog' else '2. Click `[data-submit]`'}
3. Verify `[data-loading]` appears (loading state)
4. Screenshot: "02_loading_state"
5. Wait for `[data-loading]` to disappear (timeout: 120s — Gemini API is slow)
6. Screenshot: "03_content_loaded"

#### STEP 3: Overview Tab
1. Verify `[data-content="overview"]` exists
2. Read the text inside — verify it's real content about the source topic (NOT placeholder)
3. Check text length > 200 characters
4. Verify `[data-mindmap]` exists
5. Check if `[data-mindmap]` contains an SVG element with paths/nodes
6. Screenshot: "04_overview_tab"

#### STEP 4: Quiz Tab
1. Click `[data-tab="quiz"]`
2. Wait for `[data-content="quiz"]` to contain real questions (not "Generating..." or "Loading...")
   - Timeout: 60s (quiz is generated via Gemini API on tab click)
3. Verify at least one question with `?` is visible in the text
4. Verify `[data-option="0"]` through `[data-option="3"]` exist (4 answer options)
5. Click `[data-option="1"]` (select second answer)
6. Verify `[data-explanation]` appears (shows explanation after answering)
7. Read the explanation — verify it's real text (not empty)
8. Click `[data-next-question]` to go to next question
9. Verify the question text changed
10. Screenshot: "05_quiz_tab"

#### STEP 5: Flashcards Tab
1. Click `[data-tab="cards"]`
2. Wait for `[data-content="cards"]` to contain real cards (not "Generating..." or "Loading...")
   - Timeout: 60s
3. Verify `[data-card]` exists
4. Read the front text of the card — verify it's real content
5. Click `[data-card]` to flip it
6. Verify the card content changed (back side is different from front)
7. Click `[data-got-it]` or `[data-next-card]` to go to next card
8. Verify card text changed (new card)
9. Screenshot: "06_flashcards_tab"

#### STEP 6: Podcast Tab
1. Click `[data-tab="podcast"]`
2. Wait for `[data-content="podcast"]` to contain the player (not "Generating...")
   - Timeout: 180s (podcast TTS generation takes longest)
3. Verify `[data-play]` exists (play button)
4. Click `[data-toggle-transcript]` to show transcript
5. Verify at least one `[data-transcript-line]` exists
6. Read transcript text — verify speaker names ("Alex" or "Sam") appear
7. Screenshot: "07_podcast_tab"

#### STEP 7: Tutor Tab
1. Click `[data-tab="tutor"]`
2. Verify `[data-content="tutor"]` exists
3. Verify `[data-concept-select]` exists (concept dropdown)
4. Read the dropdown options — verify they're real concepts from the content
5. Select the first concept in the dropdown
6. Type "Can you explain this concept in simple terms?" into `[data-tutor-input]`
7. Click `[data-tutor-send]`
8. Wait for a new `[data-msg]` to appear from the tutor (timeout: 30s)
9. Read the tutor's response — verify it's Socratic (asks a question back or guides thinking)
10. Screenshot: "08_tutor_tab"

#### STEP 8: Floating Chat
1. Click `[data-chat-toggle]` to open the chat panel
2. Verify `[data-chat-panel]` is visible
3. Type "What is the main takeaway from this content?" into `[data-chat-input]`
4. Click `[data-chat-send]`
5. Wait for a new `[data-msg]` inside `[data-chat-panel]` (timeout: 30s)
6. Read the response — verify it relates to the source content
7. Screenshot: "09_floating_chat"

#### STEP 9: Tab Switching
1. Rapidly click through all tabs: overview → quiz → cards → podcast → tutor
2. Verify no errors appear (no blank screens, no crash)
3. Screenshot: "10_final_state"

---

### Reporting

After all steps, output a structured report:

```
===== E2E TEST REPORT =====
SOURCE: {source['label']}
URL: {source['url']}

RESULT: [PASS or FAIL]

STEP 1 - Page Load:        [PASS/FAIL] - [what you saw]
STEP 2 - Submit Source:     [PASS/FAIL] - [what you saw]
STEP 3 - Overview Tab:      [PASS/FAIL] - [what you saw]
STEP 4 - Quiz Tab:          [PASS/FAIL] - [what you saw]
STEP 5 - Flashcards Tab:    [PASS/FAIL] - [what you saw]
STEP 6 - Podcast Tab:       [PASS/FAIL] - [what you saw]
STEP 7 - Tutor Tab:         [PASS/FAIL] - [what you saw]
STEP 8 - Floating Chat:     [PASS/FAIL] - [what you saw]
STEP 9 - Tab Switching:     [PASS/FAIL] - [what you saw]

SCREENSHOTS: [list of screenshots taken]
ERRORS: [list any errors, console errors, or unexpected behavior]
CONTENT QUALITY: [brief assessment — is the generated content real and relevant?]
===========================
```

Important:
- If a step fails, continue to the next step (don't stop early)
- If the page shows an error message, capture it
- If content looks like placeholder/mock data, mark as FAIL
- Take extra screenshots of anything unexpected
"""


async def run_e2e_agent(source_key: str = "blog") -> TestResult:
    """Run intelligent E2E test via Claude agent + Playwright MCP."""
    prompt = build_e2e_prompt(source_key)

    output = ""
    async for msg in query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            cwd=str(PROJECT_ROOT),
            allowed_tools=["Bash", "Read"],
            permission_mode=PERMISSION_MODE,
            mcp_servers={
                "playwright": {
                    "command": "npx",
                    "args": ["@playwright/mcp@latest"],
                }
            },
            system_prompt=E2E_SYSTEM_PROMPT,
            model=MODEL,
            max_turns=MAX_TURNS_E2E,
        ),
    ):
        if isinstance(msg, ResultMessage):
            output = msg.result
            print(f"\n[E2E Agent] {output[:2000]}")

    # Parse results
    passed = "RESULT: PASS" in output
    errors = []
    for line in output.split("\n"):
        if "FAIL" in line:
            errors.append(line.strip())

    return TestResult(
        round_num=None,
        passed=passed,
        output=output,
        errors=errors,
    )


async def run_full_e2e_suite() -> list[TestResult]:
    """Run E2E tests across all source types (blog, YouTube, Wikipedia)."""
    results = []
    for key in TEST_SOURCES:
        print(f"\n{'='*60}")
        print(f"E2E: Testing with {TEST_SOURCES[key]['label']}")
        print(f"{'='*60}")
        result = await run_e2e_agent(source_key=key)
        results.append(result)
        status = "PASS" if result.passed else "FAIL"
        print(f"\n{TEST_SOURCES[key]['label']}: {status}")
    return results
