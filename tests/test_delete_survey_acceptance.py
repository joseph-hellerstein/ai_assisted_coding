"""End-to-end acceptance test for the Survey Maker "Delete Survey" feature.

Run directly against a self-started server (matching this repo's existing
Playwright script convention — not pytest-collected, see pytest.ini):

    python3 tests/test_delete_survey_acceptance.py

Saves a survey, deletes it through the real UI (button -> confirm dialog),
and verifies it disappears from the dropdown, its file is removed from
disk, and the editor is reset.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _server_helper import start_server, stop_server  # noqa: E402

ROOT = Path(__file__).parent.parent
SURVEYS_DIR = ROOT / "surveys"
PORT = 8054
URL = f"http://127.0.0.1:{PORT}"


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

        # --- Create and save a survey to delete. ---
        await page.fill("#maker-title", "")
        await page.type("#maker-title", "Survey To Delete", delay=5)
        await page.click("#maker-add-question")
        await page.wait_for_timeout(300)

        before = surveys_before()
        await page.click("#maker-save-survey")
        await page.wait_for_timeout(800)

        saved_path = newest_survey_file(before)
        survey_title = "Survey To Delete"

        # --- Clicking Delete Survey with nothing selected should warn, not delete. ---
        await page.click("#maker-delete-survey")
        await page.wait_for_timeout(300)
        status_text = (await page.locator("#maker-status").inner_text()).strip()
        if "select" not in status_text.lower():
            errors.append(f"Delete Survey with nothing selected should warn to select one, got: {status_text!r}")
        if not saved_path.exists():
            errors.append("Survey file was deleted even though no survey was selected in the dropdown.")

        # --- Select the survey, then Delete Survey should open a confirm dialog. ---
        await page.click("#maker-survey-select")
        await page.wait_for_timeout(300)
        await page.click(f"text={survey_title}")
        await page.wait_for_timeout(500)

        dialog_message = {}

        def handle_dialog(dialog):
            dialog_message["text"] = dialog.message
            asyncio.create_task(dialog.accept())

        page.on("dialog", handle_dialog)

        await page.click("#maker-delete-survey")
        await page.wait_for_timeout(600)

        if "text" not in dialog_message:
            errors.append("Delete Survey did not open a confirmation dialog before deleting.")
        elif survey_title not in dialog_message["text"]:
            errors.append(f"Confirmation dialog did not mention the survey title: {dialog_message['text']!r}")

        await page.wait_for_timeout(600)

        # --- After confirming, the survey file must be gone and the editor reset. ---
        if saved_path.exists():
            errors.append("Survey file still exists on disk after confirming deletion.")

        status_text = (await page.locator("#maker-status").inner_text()).strip()
        if "deleted" not in status_text.lower():
            errors.append(f"Status message after deletion was unexpected: {status_text!r}")

        title_value = await page.locator("#maker-title").input_value()
        if title_value != "":
            errors.append(f"Editor title was not cleared after deleting the loaded survey (got {title_value!r}).")

        remaining_texts = page.locator('textarea[id*="q-text"]')
        if await remaining_texts.count() != 0:
            errors.append("Question editors were not cleared after deleting the loaded survey.")

        # The deleted survey must no longer be selectable.
        await page.click("#maker-survey-select")
        await page.wait_for_timeout(300)
        still_listed = await page.get_by_text(survey_title, exact=True).count()
        if still_listed != 0:
            errors.append("Deleted survey still appears in the survey dropdown.")

        await browser.close()

    return errors


def main():
    errors = []
    proc = start_server(PORT)
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
