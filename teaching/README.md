# Survey Manager: Teaching Edition

A smaller version of the Survey Manager, built for learning. It does the same three
things as the full app (make a survey, take it, analyze the responses) with
**5 callbacks** and under 800 lines of code. The design is described in
[`docs/teaching_edition_spec.md`](../docs/teaching_edition_spec.md).

**Work from this folder.** Open `teaching/` (not the repository root) as your VSCode
folder, and run every command below from here.

## Run it

```bash
pip install -r requirements.txt
python -m src.app
```

Then open <http://127.0.0.1:8052>. (The full edition uses port 8051, so both can run
at once.)

To start with some data, run `python -m scripts.make_sample_data`. It saves two
surveys with five responses each. Surveys are saved in `surveys/` and responses in
`data/responses/`; delete those folders to start over.

## The five callbacks

All five are in `src/app.py`.

| # | Callback | Runs when... | Updates |
|---|---|---|---|
| 1 | `save_survey_callback` | **Save Survey** is clicked | the Maker's status line |
| 2 | `refresh_survey_lists` | the page loads or a tab is chosen | the survey dropdowns on the Taker and Analyzer tabs |
| 3 | `show_survey` | a survey is chosen in the Taker | the Taker's form |
| 4 | `submit_survey_response` | **Submit** is clicked | the Taker's status line and the Submit button |
| 5 | `analyze_survey` | a survey is chosen in the Analyzer | the Analyzer's charts and table |

## Code layout

| File | What it does |
|---|---|
| `src/app.py` | Creates the app and its tabs, and defines the 5 callbacks |
| `src/models.py` | `Survey`, `Question` and `Response` |
| `src/storage.py` | Saves and loads surveys and responses as JSON files |
| `src/form_logic.py` | Pure helpers: checking the Maker's questions, checking an ID, collecting answers |
| `src/survey_maker.py` | The Survey Maker tab |
| `src/survey_taker.py` | The Survey Taker tab and the form for one survey |
| `src/survey_analyzer.py` | The Survey Analyzer tab, its charts and its table |
| `src/constants.py` | Component ids and settings |

## Test it

```bash
pytest
```

There's also an end-to-end check that drives the app in a real browser:

```bash
pip install playwright && playwright install chromium   # once
python tests/e2e_check.py
```
