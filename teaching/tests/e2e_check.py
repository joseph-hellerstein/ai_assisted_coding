"""End-to-end check of the teaching edition in a real browser.

Not collected by pytest. Run it from the teaching/ folder:

    pip install playwright && playwright install chromium   # once
    python tests/e2e_check.py

It starts the app on port 8062 with its data in a temporary folder (so your
own surveys are untouched), then makes a survey, answers it, and analyzes it.
Exit code 0 means every step passed.
"""
import json
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

TEACHING_DIR = Path(__file__).parent.parent
PORT = 8062
URL = f"http://127.0.0.1:{PORT}"
LAUNCHER = (
    "import sys, pathlib; sys.path.insert(0, '.'); import src.storage as st; "
    "d = pathlib.Path(sys.argv[1]); st.SURVEYS_DIR = d / 'surveys'; st.RESPONSES_DIR = d / 'responses'; "
    f"from src.app import app; app.run(port={PORT}, debug=False)"
)


def check(condition, message):
    if not condition:
        raise AssertionError(message)
    print(f"OK   {message}")


def row_field(page, field, row):
    return page.locator(f'id={{"row":{row},"type":"maker-q-{field}"}}')


def run(page, data_dir):
    responses = lambda: list((data_dir / "responses").glob("*/*.json"))

    # 1. Make a survey: text, blank row, checkbox, yesno.
    page.goto(URL)
    page.fill("#maker-title", "E2E")
    row_field(page, "text", 0).fill("Comments?")
    row_field(page, "type", 2).click()
    page.get_by_text("checkbox", exact=True).last.click()
    row_field(page, "text", 2).fill("Colors?")
    row_field(page, "options", 2).fill("Red\nBlue")
    row_field(page, "type", 3).click()
    page.get_by_text("yesno", exact=True).last.click()
    row_field(page, "text", 3).fill("Attended?")
    page.click("#maker-save")
    page.wait_for_timeout(800)
    check("✅" in page.inner_text("#maker-status"), "survey saved")
    [survey_file] = list((data_dir / "surveys").glob("*.json"))
    questions = json.loads(survey_file.read_text())["questions"]
    check([(q["type"], q["text"]) for q in questions]
          == [("text", "Comments?"), ("checkbox", "Colors?"), ("yesno", "Attended?")],
          "saved survey has 3 questions in row order")

    # 2. Choose it in the Survey Taker. Nothing should be submitted just by showing the form.
    page.get_by_text("Survey Taker", exact=True).click()
    page.click("#taker-survey-select")
    page.get_by_text("E2E", exact=True).last.click()
    page.wait_for_timeout(1500)
    check(page.locator('[id*="\\"type\\":\\"answer\\""]').count() == 3, "form shows 3 answer inputs")
    check(page.inner_text("#taker-status") == "" and not responses(),
          "showing the form submits nothing")

    # 3. A bad ID is rejected, visibly, and nothing is saved.
    page.fill("#taker-respondent-id", "12")
    page.click("#taker-submit")
    page.wait_for_timeout(800)
    check("Your ID must be exactly 5 digits." in page.inner_text("#taker-status")
          and page.locator("#taker-status").is_visible(), "bad ID message is visible")
    check(not page.is_disabled("#taker-submit") and not responses(), "bad ID saves nothing")

    # 4. A good ID is accepted.
    page.fill("#taker-respondent-id", "12345")
    page.get_by_label("Red").check()
    page.get_by_label("Yes").check()
    page.click("#taker-submit")
    page.wait_for_timeout(800)
    check("Thank you" in page.inner_text("#taker-status"), "thank-you message shown")
    check(page.is_disabled("#taker-submit") and len(responses()) == 1, "response saved, Submit disabled")

    # 5. The Analyzer shows it.
    page.get_by_text("Survey Analyzer", exact=True).click()
    page.click("#analyzer-survey-select")
    page.get_by_text("E2E", exact=True).last.click()
    page.wait_for_timeout(1500)
    results = page.locator("#analyzer-results")
    check("Responses: 1" in results.inner_text(), "Analyzer shows 1 response")
    check(results.locator(".js-plotly-plot").count() == 3, "Analyzer shows 3 charts")
    check(results.locator("td[data-dash-column='respondent_id']").count() == 1, "table has 1 row")


def main():
    with tempfile.TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        server = subprocess.Popen([sys.executable, "-c", LAUNCHER, str(data_dir)], cwd=TEACHING_DIR,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            for _ in range(60):
                try:
                    urllib.request.urlopen(URL)
                    break
                except OSError:
                    time.sleep(0.25)
            with sync_playwright() as pw:
                browser = pw.chromium.launch()
                run(browser.new_page(), data_dir)
                browser.close()
        finally:
            server.terminate()
            server.wait()
    print("All end-to-end checks passed.")


if __name__ == "__main__":
    main()
