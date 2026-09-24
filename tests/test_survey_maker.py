"""Ad-hoc Playwright script: quick diagnostic pass over the Survey Maker
Add-Question / Save flow. Self-starts its own server (matching the other
scripts in this directory), so it needs nothing running beforehand:

    python3 tests/test_survey_maker.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _server_helper import start_server, stop_server  # noqa: E402

PORT = 8056
URL = f"http://127.0.0.1:{PORT}"


async def test_survey_maker():
    from playwright.async_api import async_playwright

    print('=== Test Survey Maker flow ===', flush=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1400, "height": 900})
        await page.goto(URL)

        print('Clicking Survey Maker tab...', flush=True)
        await page.click("text=Survey Maker", timeout=5000)
        await page.wait_for_timeout(500)

        # Type title and description — the id is on the input/textarea
        # element itself, not a wrapping container.
        title_input = page.locator("#maker-title")
        await title_input.fill("Test Survey")
        print(f'Title: {await title_input.input_value()}', flush=True)

        desc_ta = page.locator("#maker-description")
        await desc_ta.fill("This is a test.")
        print(f'Desc: {await desc_ta.input_value()}', flush=True)

        # Click Add Question and wait for callback to process
        add_btn = page.locator("#maker-add-question")
        await add_btn.click()
        await page.wait_for_timeout(500)

        q_info = await page.evaluate("""() => {
            const container = document.querySelector('#maker-questions-container');
            if (!container) return {error: "no container", children_count: 0};
            let elements = [];
            for (let i=0; i<Math.min(container.children.length, 5); i++) {
                const c = container.children[i];
                elements.push({tag: c.tagName, id: c.id||'', cls: String(c.className||'').substring(0,80), child_count: c.children.length});
            }
            return {children_count: container.children.length, elements: elements};
        }""")
        print(f'Questions DOM: {q_info}', flush=True)

        # Save survey
        print('Clicking Save Survey...', flush=True)
        await page.click("#maker-save-survey", timeout=5000)
        await page.wait_for_timeout(500)
        status = await page.locator("#maker-status").inner_text()
        print(f'Status: {repr(status)}', flush=True)

        # Check dropdown options after save (options refresh on tab switch)
        dd_info = await page.evaluate("""() => {
            const dd = document.querySelector('[id*="maker-survey-select"]');
            if (!dd) return {found: false};
            return {found: true, tag: dd.tagName, cls: String(dd.className||'')};
        }""")
        print(f'Dropdown after save: {dd_info}', flush=True)

        await browser.close()
    print('=== Done ===', flush=True)


def main():
    proc = start_server(PORT)
    try:
        asyncio.run(test_survey_maker())
    finally:
        stop_server(proc)


if __name__ == "__main__":
    main()
