import asyncio, sys


async def main():
    from playwright.async_api import async_playwright
    errors = []
    warnings = []

    url = "http://127.0.0.1:8050"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1400, "height": 900})
        print("Browser started. Navigating to", url)

        try:
            errors, warnings = await run_tests(page, errors, warnings)
        except Exception as e:
            import traceback
            traceback.print_exc()
            errors.append("FATAL test runner exception: {}".format(e))
        finally:
            await browser.close()

    return errors, warnings


async def run_tests(page, errors, warnings):
    url = "http://127.0.0.1:8050"

    print("\n=== TEST 1: Initial page load and tab structure ===")
    await page.goto(url)
    await page.wait_for_selector("#main-tabs", timeout=5000)
    h1 = await page.locator("h1").first.inner_text()
    print("  Page H1:", repr(h1))
    if "Survey Manager" not in h1:
        errors.append("H1 text unexpected: {} (expected 'Survey Manager')".format(repr(h1)))
    tabs = await page.locator(".dcc-tabs .dcc-tab").all()
    print("  Found {} tabs".format(len(tabs)))
    if len(tabs) != 3:
        errors.append("Expected 3 tabs, found {}".format(len(tabs)))
    tab_labels = [await t.inner_text() for t in tabs]
    print("  Tab labels:", tab_labels)



    # === TEST 2: Survey Maker tab - basic interaction ===
    print("\n=== TEST 2: Survey Maker tab ===")
    await page.click("text=Survey Maker")
    await page.wait_for_selector("#maker-title", timeout=5000)

    title_input = page.locator("#maker-title")
    await title_input.fill("")
    await title_input.type("Test Survey", delay=20)
    print("  Title value:", repr(await title_input.input_value()))

    desc_ta = page.locator("#maker-description")
    await desc_ta.fill("")
    await desc_ta.type("This is a test survey.", delay=20)
    print("  Description value:", repr(await desc_ta.input_value()))

    add_q_btn = page.locator("#maker-add-question")
    for i in range(3):
        await add_q_btn.click()
        await page.wait_for_timeout(500)
    print("  Clicked Add Question 3 times.")

    # Save Survey button
    print("\n  Clicking Save Survey...")
    save_btn = page.locator("#maker-save-survey")
    await save_btn.click()
    await page.wait_for_timeout(1000)
    status = await page.locator("#maker-status").inner_text()
    print("  Status message after save:", repr(status))



    # === TEST 3: Survey Taker tab ===
    print("\n=== TEST 3: Survey Taker tab ===")
    await page.click("text=Survey Taker")
    await page.wait_for_selector("#taker-survey-select", timeout=5000)

    taker_dd = page.locator("#taker-survey-select .css-1gspdo7")
    dd_text = await taker_dd.inner_text()
    print("  Taker dropdown content:", repr(dd_text.strip()))

    if "Test Survey" in dd_text:
        await page.click("#taker-survey-select", position={"x": 50, "y": 10})
        await page.wait_for_timeout(500)
        n_dd_opts = await page.locator("#taker-survey-select .css-14lo706 li").count()
        print("  Dropdown options visible:", n_dd_opts)

        if n_dd_opts > 0:
            await page.click("#taker-survey-select .css-14lo706 li")
            await page.wait_for_timeout(800)

            form_div = page.locator("#taker-survey-form")
            form_html_len = len(await form_div.inner_html())
            print("  Taker survey form HTML length:", form_html_len)

            radios = await page.locator(".dcc-radio-item").count()
            checks = await page.locator(".dcc-checklist-item").count()
            textareas_count = await page.locator("textarea").count()
            print("    Radio items:", radios, "Checklist items:", checks, "Textareas:", textareas_count)

            taker_submit_btn = page.locator("#taker-submit")
            n_taker_submits = await taker_submit_btn.count()
            print("  Submit survey button visible:", bool(n_taker_submits))

            form_inputs = page.locator("#taker-survey-form input[type=text], #taker-survey-form textarea")
            n_form_inputs = await form_inputs.count()
            print("  Form text inputs/textareas count:", n_form_inputs)

            for fi in range(n_form_inputs):
                inp = form_inputs.nth(fi)
                tag = await inp.evaluate("el => el.tagName")
                try:
                    await inp.fill("")
                    await inp.type("Answer to question {}".format(fi + 1), delay=20)
                    print("    Filled input #{} (tag={}) with text.".format(fi, tag))
                except Exception as e:
                    errors.append("Taker form input #{} fill/type error: {}".format(fi, e))

            # Submit Survey button
            print("\n  Clicking Submit Survey...")
            await taker_submit_btn.click()
            await page.wait_for_timeout(1000)
            thankyou = await page.locator("#taker-thankyou").inner_html()
            print("  Thank-you div HTML:", repr(thankyou.strip()))
    else:
        warnings.append("Test Survey not found in Taker dropdown. Content was: {}".format(repr(dd_text.strip())))



    # === TEST 4: Tab switch refreshes dropdown lists ===
    print("\n=== TEST 4: Tab switch refreshes dropdowns ===")
    await page.click("text=Survey Maker")
    await page.wait_for_timeout(800)
    maker_dd = page.locator("#maker-survey-select .css-1gspdo7")
    maker_dd_text = await maker_dd.inner_text()
    print("  Maker dropdown after switch:", repr(maker_dd_text.strip()))

    # === TEST 5: Survey Analyzer tab ===
    print("\n=== TEST 5: Survey Analyzer tab ===")
    await page.click("text=Survey Analyzer")
    await page.wait_for_selector("#analyzer-survey-select", timeout=5000)
    analyzer_dd = page.locator("#analyzer-survey-select .css-1gspdo7")
    analyzer_dd_text = await analyzer_dd.inner_text()
    print("  Analyzer dropdown content:", repr(analyzer_dd_text.strip()))

    if "Test Survey" in analyzer_dd_text:
        await page.click("#analyzer-survey-select", position={"x": 50, "y": 10})
        await page.wait_for_timeout(500)
        n_an_opts = await page.locator("#analyzer-survey-select .css-14lo706 li").count()
        print("  Analyzer dropdown options visible:", n_an_opts)

        if n_an_opts > 0:
            await page.click("#analyzer-survey-select .css-14lo706 li")
            await page.wait_for_timeout(800)

            resp_count = await page.locator("#analyzer-response-count").inner_text()
            print("  Response count header:", repr(resp_count))

            dt_cells = page.locator("#analyzer-data-table .dash-spreadsheet-container, #analyzer-data-table .dash-cell")
            n_dt_cells = await dt_cells.count()
            print("  Data table cells found:", n_dt_cells)

    return errors, warnings


if __name__ == "__main__":
    import traceback as tb

    errors, warnings = asyncio.run(main())

    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    if not errors and not warnings:
        print("All tests passed with no errors or warnings.")
    else:
        if warnings:
            for ww in warnings:
                print("WARNING: {}".format(ww))
        if errors:
            print("\nERRORS ({}):".format(len(errors)))
            for i, e in enumerate(errors, 1):
                print("  {}. {}".format(i, e))

