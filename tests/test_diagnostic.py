import asyncio, sys, os, json
sys.path.insert(0, "/Users/jlheller/home/Technical/repos/ai_assisted_coding/src")
from playwright.async_api import async_playwright

async def main():
    print("=== Diagnostic Test ===", flush=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, timeout=10000)
        page = await browser.new_page(viewport={"width": 1400, "height": 900})
        resp = await asyncio.wait_for(page.goto("http://127.0.0.1:8050"), timeout=15000)
        print(f"Response: {resp.status}", flush=True)

        # Check body structure for dcc.Store rendering
        body_info = await page.evaluate("""() => {
            const root = document.getElementById('root');
            let result = {};
            if (root) {
                result.root_tag = root.tagName;
                result.root_children = root.children.length;
                result.tabs_in_root = Array.from(root.querySelectorAll('.tab')).length;
            }
            const storeEls = document.querySelectorAll('[class*=store], [id*=store]');
            result.store_elements = storeEls.length;
            // Check for dash-store class anywhere
            result.dash_store_class = document.querySelectorAll('.dash-store').length;
            return result;
        }""")
        print(f'Body info: {body_info}', flush=True)

        # Click Survey Maker tab
        await page.click('#main-tabs > div.tab >> text=Survey Maker', timeout=5000)
        await page.wait_for_timeout(1500)

        # Check maker DOM state
        maker_info = await page.evaluate("""() => {
            const container = document.querySelector('#maker-questions-container');
            let result = {};
            if (container) {
                result.container_tag = container.tagName;
                result.container_children = container.children.length;
            } else { result.container_missing = True; }
            const mdata = document.getElementById('maker-survey-data');
            result.maker_survey_data_exists = !!mdata;
            if (mdata) {
                result.mdata_tag = mdata.tagName;
                result.mdata_cls = String(mdata.className || '');
            }
            return result;
        }""")
        print(f'Maker DOM: {maker_info}', flush=True)

        # Type title using proper JS event dispatch
        await page.evaluate("""() => {
            const el = document.querySelector('#maker-title input');
            if (el) {
                Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(el, 'Test Survey');
                el.dispatchEvent(new Event('input', {bubbles: true}));
                el.dispatchEvent(new Event('change', {bubbles: true}));
            }
        }""")

        title_val = await page.locator('#maker-title input').input_value()
        print(f'Title value after JS dispatch: {repr(title_val)}', flush=True)

        # Click Add Question 3 times and check children count each time
        for i in range(3):
            await page.click('#maker-add-question', timeout=5000)
            await page.wait_for_timeout(1000)
            n = await page.evaluate("""() => { const c = document.querySelector('#maker-questions-container'); return c ? c.children.length : -1; }""")
            print(f'  Add #{i+1}: children={n}', flush=True)

        # Check store data via React fiber inspection
        store_val = await page.evaluate("""() => {
            const el = document.getElementById('maker-survey-data');
            if (!el) return 'ELEMENT_NOT_FOUND';
            try {
                let node = el;
                while (node && !node._react Fiber) { node = node.__react_fiber || node.nextSibling; }
                // Dash Store stores data in memoizedProps.data
                const fiber = el.__reactInternals || el.__reactFiber || findFiber(el);
                if (fiber?.memoizedProps?.data !== undefined) return fiber.memoizedProps.data;
            } catch(e) {}
            return 'CANNOT_READ';
        }""")
        print(f'Store data: {store_val}', flush=True)

        # Click Save Survey
        await page.click('#maker-save-survey', timeout=5000)
        await page.wait_for_timeout(1000)
        status = await page.locator('#maker-status').inner_text()
        print(f'Save status: {repr(status)}', flush=True)

        # Check if survey was saved to disk
        try:
            files = os.listdir('/Users/jlheller/home/Technical/repos/ai_assisted_coding/surveys')
            print(f'Survey files on disk: {files}', flush=True)
            for f in sorted(files):
                if f.endswith('.json'):
                    with open(os.path.join('/Users/jlheller/home/Technical/repos/ai_assisted_coding/surveys', f)) as fp:
                        data = json.load(fp)
                        print(f'  {f}: title={data.get("title")}, questions={len(data.get("questions", []))}', flush=True)
        except Exception as e:
            print(f'Disk check error: {e}', flush=True)

        await browser.close()
    print('=== Done ===', flush=True)

asyncio.run(main())
