import asyncio, sys
sys.path.insert(0, '/Users/jjheller/home/Technical/repos/ai_assisted_coding/src')
from playwright.async_api import async_playwright

async def test_survey_maker():
    print('=== Test Survey Maker flow ===', flush=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1400, "height": 900})
        await page.goto("http://127.0.0.1:8050")
        
        # Click Survey Maker tab using correct selector
        print('Clicking Survey Maker tab...', flush=True)
        await page.click("#main-tabs > div.tab >> text=Survey Maker", timeout=3000)
        await page.wait_for_timeout(1500)

        # Type title and description
        title_input = page.locator("#maker-title input")
        await title_input.fill("Test Survey")
        print(f'Title: {await title_input.input_value()}', flush=True)
        
        desc_ta = page.locator("#maker-description textarea")
        await desc_ta.fill("This is a test.")
        print(f'Desc: {await desc_ta.input_value()}', flush=True)

        # Click Add Question and wait for callback to process
        add_btn = page.locator("#maker-add-question")
        await add_btn.click()
        await page.wait_for_timeout(2000)
        
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
        await page.wait_for_timeout(1000)
        status = await page.locator("#maker-status").inner_text()
        print(f'Status: {repr(status)}', flush=True)

        # Check dropdown options after save (might need tab switch to refresh)
        dd_info = await page.evaluate("""() => {
            const dd = document.querySelector('#maker-survey-select');
            if (!dd) return {found: false};
            let txt = '';
            for (let i=0; i<dd.children.length; i++) {
                txt += (dd.children[i].textContent||'').substring(0,50) + '|';
            }
            return {found: true, tag: dd.tagName, cls: String(dd.className||'')};
        }""")
        print(f'Dropdown after save: {dd_info}', flush=True)

        await browser.close()
    print('=== Done ===', flush=True)

asyncio.run(test_survey_maker())
