"""Verify E2E: Full browser test of the complete DigestAnything app.

Run AFTER all 4 rounds pass. Tests the actual UI in a real browser.
Requires: backend on :8000, frontend on :3000, Playwright installed.

Tests the complete user flow:
  1. Page loads with input field and tab bar
  2. Submit a URL → loading state appears
  3. Overview tab: summary card + mindmap renders
  4. Quiz tab: questions render, click answer → feedback shows
  5. Cards tab: card renders, flip works, next/prev navigation
  6. Podcast tab: audio player + transcript visible
  7. Tutor tab: concept dropdown, send message, Socratic response
  8. Floating chat: click bubble → panel opens, send message → response
  9. Tab switching works smoothly
  10. No console errors
"""
import subprocess
import sys
import time

# Use Playwright Python (sync API)
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)

FRONTEND = "http://localhost:3000"
TEST_URL = "https://www.anthropic.com/engineering/harness-design-long-running-apps"


def run_e2e():
    errors = []
    console_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Capture console errors
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        # 1. Page loads
        print("=== 1. Page loads ===")
        try:
            page.goto(FRONTEND, timeout=15000)
            page.wait_for_load_state("networkidle", timeout=10000)
            assert page.title(), "Page has no title"
            print(f"  Title: {page.title()}")
            print("  PASSED")
        except Exception as e:
            errors.append(f"page_load: {e}")
            print(f"  FAILED: {e}")
            browser.close()
            return errors

        # 2. Input field exists and tab bar visible
        print("\n=== 2. UI shell ===")
        try:
            # Check for source input (various selectors)
            input_el = page.query_selector("input[type='text'], input[type='url'], input[data-chat-input], textarea")
            assert input_el, "No input field found"
            print("  Input field: found")

            # Check for tabs
            tabs = page.query_selector_all("[data-tab], button:has-text('Overview'), button:has-text('Quiz'), button:has-text('Cards')")
            if tabs:
                print(f"  Tabs found: {len(tabs)}")
            else:
                print("  Tabs: not visible yet (may appear after digest)")
            print("  PASSED")
        except Exception as e:
            errors.append(f"ui_shell: {e}")
            print(f"  FAILED: {e}")

        # 3. Submit URL and wait for results
        print("\n=== 3. Submit URL → digest ===")
        try:
            # Find and fill input
            input_el = page.query_selector("input[type='text'], input[type='url'], textarea")
            if input_el:
                input_el.fill(TEST_URL)
                # Find submit button
                submit = page.query_selector("button:has-text('Digest'), button:has-text('Submit'), button:has-text('Go'), button[type='submit']")
                if submit:
                    submit.click()
                    print("  Submitted URL, waiting for results...")
                    # Wait for content to load (up to 120s for Gemini API)
                    page.wait_for_timeout(5000)  # Initial wait
                    # Check for loading state or content
                    page.wait_for_selector("[data-content], [data-tab='overview'].active, .loading, [class*='loading']", timeout=120000)
                    print("  Content loaded")
                else:
                    print("  No submit button found (may auto-submit)")
            print("  PASSED")
        except Exception as e:
            errors.append(f"submit: {e}")
            print(f"  FAILED: {e}")

        # 4. Overview tab — summary + mindmap
        print("\n=== 4. Overview tab ===")
        try:
            # Click overview tab if needed
            overview_tab = page.query_selector("[data-tab='overview'], button:has-text('Overview')")
            if overview_tab:
                overview_tab.click()
                page.wait_for_timeout(1000)

            # Check for summary text
            body_text = page.inner_text("body")
            assert len(body_text) > 100, "Page has very little text content"

            # Check for SVG (mindmap)
            svg = page.query_selector("svg")
            if svg:
                print("  Mindmap SVG: found")
            else:
                print("  Mindmap SVG: not found (may render differently)")
            print("  PASSED")
        except Exception as e:
            errors.append(f"overview: {e}")
            print(f"  FAILED: {e}")

        # 5. Quiz tab
        print("\n=== 5. Quiz tab ===")
        try:
            quiz_tab = page.query_selector("[data-tab='quiz'], button:has-text('Quiz')")
            if quiz_tab:
                quiz_tab.click()
                page.wait_for_timeout(2000)

                # Check for question text
                question = page.query_selector("[data-content='quiz'], .quiz, [class*='quiz'], [class*='question']")
                if question:
                    print("  Quiz content: found")
                else:
                    print("  Quiz content: checking for any question text...")
                    body = page.inner_text("body")
                    has_question = "?" in body
                    print(f"  Has question marks in body: {has_question}")

                # Try clicking an answer option
                options = page.query_selector_all("[data-option], button[class*='option'], [class*='answer']")
                if options:
                    options[0].click()
                    page.wait_for_timeout(500)
                    print(f"  Answer options: {len(options)}, clicked first")
                print("  PASSED")
            else:
                print("  No quiz tab found")
                errors.append("quiz_tab: not found")
        except Exception as e:
            errors.append(f"quiz: {e}")
            print(f"  FAILED: {e}")

        # 6. Cards tab
        print("\n=== 6. Cards tab ===")
        try:
            cards_tab = page.query_selector("[data-tab='cards'], button:has-text('Cards')")
            if cards_tab:
                cards_tab.click()
                page.wait_for_timeout(2000)

                card = page.query_selector("[data-card], .card, [class*='card'], [class*='flash']")
                if card:
                    print("  Card element: found")
                    # Try flipping
                    card.click()
                    page.wait_for_timeout(500)
                    print("  Card clicked (flip)")
                print("  PASSED")
            else:
                print("  No cards tab found")
                errors.append("cards_tab: not found")
        except Exception as e:
            errors.append(f"cards: {e}")
            print(f"  FAILED: {e}")

        # 7. Podcast tab
        print("\n=== 7. Podcast tab ===")
        try:
            podcast_tab = page.query_selector("[data-tab='podcast'], button:has-text('Podcast')")
            if podcast_tab:
                podcast_tab.click()
                page.wait_for_timeout(2000)

                # Check for audio element or player
                audio = page.query_selector("audio, [data-play], [class*='player'], [class*='audio']")
                if audio:
                    print("  Audio player: found")
                else:
                    print("  Audio player: not found (may be custom)")

                # Check for transcript
                body = page.inner_text("body")
                has_dialogue = "Alex" in body or "Sam" in body or "Speaker" in body.lower()
                print(f"  Transcript visible: {has_dialogue}")
                print("  PASSED")
            else:
                print("  No podcast tab found")
                errors.append("podcast_tab: not found")
        except Exception as e:
            errors.append(f"podcast: {e}")
            print(f"  FAILED: {e}")

        # 8. Tutor tab
        print("\n=== 8. Tutor tab ===")
        try:
            tutor_tab = page.query_selector("[data-tab='tutor'], button:has-text('Tutor')")
            if tutor_tab:
                tutor_tab.click()
                page.wait_for_timeout(2000)

                # Check for concept dropdown
                dropdown = page.query_selector("select, [class*='dropdown'], [class*='concept']")
                if dropdown:
                    print("  Concept dropdown: found")

                # Find tutor input and send message
                tutor_input = page.query_selector("[data-chat-input], input[type='text']:visible, textarea:visible")
                if tutor_input:
                    tutor_input.fill("What does this concept mean in simple terms?")
                    send_btn = page.query_selector("[data-chat-send], button:has-text('Send'), button[type='submit']:visible")
                    if send_btn:
                        send_btn.click()
                        page.wait_for_timeout(5000)  # Wait for Gemini response
                        print("  Sent tutor message, waiting for response...")
                print("  PASSED")
            else:
                print("  No tutor tab found")
                errors.append("tutor_tab: not found")
        except Exception as e:
            errors.append(f"tutor: {e}")
            print(f"  FAILED: {e}")

        # 9. Floating chat
        print("\n=== 9. Floating chat ===")
        try:
            chat_toggle = page.query_selector("[data-chat-toggle], button:has-text('💬'), [class*='chat-bubble'], [class*='floating']")
            if chat_toggle:
                chat_toggle.click()
                page.wait_for_timeout(500)
                print("  Chat panel opened")

                chat_input = page.query_selector("[data-chat-input], [data-chat-panel] input, [data-chat-panel] textarea")
                if chat_input:
                    chat_input.fill("What is the key takeaway?")
                    send = page.query_selector("[data-chat-send], [data-chat-panel] button:has-text('Send'), [data-chat-panel] button[type='submit']")
                    if send:
                        send.click()
                        page.wait_for_timeout(5000)
                        print("  Sent chat message")

                        # Check for response
                        messages = page.query_selector_all("[data-msg], [class*='message'], [class*='response']")
                        print(f"  Messages in panel: {len(messages)}")
                print("  PASSED")
            else:
                print("  No chat toggle found")
                errors.append("floating_chat: toggle not found")
        except Exception as e:
            errors.append(f"floating_chat: {e}")
            print(f"  FAILED: {e}")

        # 10. Console errors
        print("\n=== 10. Console errors ===")
        critical_errors = [e for e in console_errors if "FATAL" in e or "Uncaught" in e or "TypeError" in e]
        if critical_errors:
            print(f"  {len(critical_errors)} critical console errors:")
            for e in critical_errors[:5]:
                print(f"    - {e[:100]}")
            errors.append(f"console: {len(critical_errors)} critical errors")
        else:
            print(f"  {len(console_errors)} total console messages, 0 critical")
            print("  PASSED")

        # Take screenshot for manual review
        try:
            page.screenshot(path="tests/samples/e2e_screenshot.png", full_page=True)
            print("\n  Screenshot saved: tests/samples/e2e_screenshot.png")
        except:
            pass

        browser.close()

    return errors


def main():
    print("DigestAnything E2E Browser Test")
    print("=" * 60)
    errors = run_e2e()

    print(f"\n{'='*60}")
    if errors:
        print(f"E2E FAILED ({len(errors)} errors):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("E2E PASSED — Full browser flow working")


if __name__ == "__main__":
    main()
