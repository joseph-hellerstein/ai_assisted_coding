"""End-to-end acceptance test for the Survey Maker bug fixes.

Run directly against a self-started server (matching this repo's existing
Playwright script convention — not pytest-collected, see pytest.ini):

    python3 tests/test_bugfix_acceptance.py

Exercises the actual originally-reported symptom (typed question text/
options not being retained) plus the other fixed bugs, end to end through
the real running app: add-question preserving prior edits, type-switch
revealing the options editor, delete-question, save+reload round-trip, and
survey-taker submit actually persisting a response.
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _server_helper import start_server as _start_server, stop_server  # noqa: E402

ROOT = Path(__file__).parent.parent
SURVEYS_DIR = ROOT / "surveys"
RESPONSES_DIR = ROOT / "data" / "responses"
PORT = 8052
URL = f"http://127.0.0.1:{PORT}"


def start_server():
    return _start_server(PORT)


def surveys_before():
    if not SURVEYS_DIR.exists():
        return set()
    return {p.name for p in SURVEYS_DIR.glob("*.json")}


def newest_survey_file(before):
    after = {p.name for p in SURVEYS_DIR.glob("*.json")}
    new_names = after - before
    assert new_names, "No new survey file was written by Save Survey."
    assert len(new_names) == 1, f"Expected exactly one new survey file, got {new_names}"
    return SURVEYS_DIR / next(iter(new_names))


async def run(errors):
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1400, "height": 900})

        await page.goto(URL)
        await page.wait_for_selector("#main-tabs", timeout=5000)
        await page.click("text=Survey Maker")
        await page.wait_for_selector("#maker-title", timeout=5000)

        # --- Bug #1/#7 regression: typed question text/options must be
        # captured by Save, not silently discarded. ---
        await page.fill("#maker-title", "")
        await page.type("#maker-title", "Acceptance Test Survey", delay=5)
        await page.fill("#maker-description", "")
        await page.type("#maker-description", "Checking the fix.", delay=5)

        # First question already exists after page load? No — Maker starts
        # with zero questions until Add/Create. Use Add Question.
        await page.click("#maker-add-question")
        await page.wait_for_timeout(300)

        text_inputs = page.locator('textarea[id*="q-text"]')
        await text_inputs.first.fill("")
        await text_inputs.first.type("How satisfied are you?", delay=5)

        # Switch this question's type to Checkboxes — bug #3 regression:
        # the options textarea must become visible without a page reload.
        type_dropdown = page.locator('button[id*="q-type"]').first
        await type_dropdown.click()
        await page.wait_for_timeout(300)
        await page.get_by_text("Checkboxes (select all that apply)", exact=True).click()
        await page.wait_for_timeout(400)

        options_textarea = page.locator('textarea[id*="q-options"]').first
        visible = await options_textarea.is_visible()
        if not visible:
            errors.append("BUG #3 NOT FIXED: options textarea did not become visible after switching type to Checkboxes.")
        else:
            await options_textarea.fill("")
            await options_textarea.type("Red\nGreen\nBlue", delay=5)

        # --- Bug #2 regression: Add Question must not wipe this question's
        # already-typed content. ---
        await page.click("#maker-add-question")
        await page.wait_for_timeout(300)

        first_text_value = await text_inputs.first.input_value()
        if first_text_value != "How satisfied are you?":
            errors.append(
                f"BUG #2 NOT FIXED: first question's text was wiped by Add Question "
                f"(got {first_text_value!r})."
            )

        second_text_inputs = page.locator('textarea[id*="q-text"]')
        await second_text_inputs.nth(1).fill("")
        await second_text_inputs.nth(1).type("Second question text", delay=5)

        # --- Bug #4 regression: Delete Question must actually remove a
        # question (and only that one). ---
        delete_buttons = page.locator('button[id*="delete-q"]')
        count_before_delete = await delete_buttons.count()
        await delete_buttons.nth(1).click()
        await page.wait_for_timeout(300)
        count_after_delete = await delete_buttons.count()
        if count_after_delete != count_before_delete - 1:
            errors.append(
                f"BUG #4 NOT FIXED: Delete Question did not remove exactly one question "
                f"(before={count_before_delete}, after={count_after_delete})."
            )
        remaining_text = await page.locator('textarea[id*="q-text"]').first.input_value()
        if remaining_text != "How satisfied are you?":
            errors.append(
                f"BUG #4 NOT FIXED: deleting a question corrupted the remaining question's text "
                f"(got {remaining_text!r})."
            )

        # --- Save and verify what actually hit disk. ---
        before = surveys_before()
        await page.click("#maker-save-survey")
        await page.wait_for_timeout(800)
        status_text = (await page.locator("#maker-status").inner_text()).strip()
        if "saved successfully" not in status_text.lower():
            errors.append(f"Save did not report success: {status_text!r}")

        try:
            saved_path = newest_survey_file(before)
            saved = json.loads(saved_path.read_text())
            q_texts = [q["text"] for q in saved["questions"]]
            if "How satisfied are you?" not in q_texts:
                errors.append(
                    f"BUG #1 NOT FIXED: saved survey does not contain the typed question "
                    f"text. Saved questions: {saved['questions']}"
                )
            else:
                saved_q = next(q for q in saved["questions"] if q["text"] == "How satisfied are you?")
                if saved_q.get("options") != ["Red", "Green", "Blue"]:
                    errors.append(
                        f"BUG #1 NOT FIXED: saved question's options were not captured "
                        f"(got {saved_q.get('options')})."
                    )
            survey_id = saved["id"]
            survey_title = saved["title"]
        except AssertionError as e:
            errors.append(f"BUG #1 NOT FIXED: {e}")
            survey_id = None
            survey_title = None

        # --- Reload the saved survey and confirm the text round-trips
        # through the editor too (not just the JSON file). ---
        if survey_id:
            await page.select_option("#maker-survey-select", label=survey_title) if False else None
            # Dash dropdowns aren't plain <select>; use the dropdown UI.
            await page.click("#maker-survey-select")
            await page.wait_for_timeout(300)
            await page.click(f"text={survey_title}")
            await page.wait_for_timeout(500)
            reloaded_text = await page.locator('textarea[id*="q-text"]').first.input_value()
            if reloaded_text != "How satisfied are you?":
                errors.append(
                    f"Reloading the saved survey did not show the saved question text "
                    f"(got {reloaded_text!r})."
                )

        # --- Bug #5 regression: Survey Taker submit must actually persist
        # a Response. ---
        if survey_id:
            resp_dir = RESPONSES_DIR / survey_id
            responses_before = set(resp_dir.glob("*.json")) if resp_dir.exists() else set()

            await page.click("text=Survey Taker")
            await page.wait_for_selector("#taker-survey-select", timeout=5000)
            await page.click("#taker-survey-select")
            await page.wait_for_timeout(300)
            await page.click(f"text={survey_title}")
            await page.wait_for_timeout(500)

            taker_text_inputs = page.locator("#taker-survey-form textarea")
            if await taker_text_inputs.count() > 0:
                await taker_text_inputs.first.fill("")
                await taker_text_inputs.first.type("My answer", delay=5)

            await page.click("#taker-submit")
            await page.wait_for_timeout(800)

            responses_after = set(resp_dir.glob("*.json")) if resp_dir.exists() else set()
            if not (responses_after - responses_before):
                errors.append("BUG #5 NOT FIXED: submitting the Survey Taker form did not persist a Response file.")

        await browser.close()

    return errors


def main():
    errors = []
    proc = start_server()
    try:
        errors = asyncio.run(run(errors))
    finally:
        stop_server(proc)

    print("=" * 70)
    if errors:
        print(f"FAILED — {len(errors)} issue(s):")
        for i, e in enumerate(errors, 1):
            print(f"  {i}. {e}")
        sys.exit(1)
    else:
        print("PASSED — all acceptance checks succeeded.")
        sys.exit(0)


if __name__ == "__main__":
    main()
