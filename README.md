# AI Assisted Coding

This repo develops content for the short course **AI Assisted Coding**.

The content consists of a sequence of episodes that describe the material presented. Episodes are markdown files in the `course_materials/episodes` folder. That folder also contains the other course materials (audience, learning objectives, course outline, etc.).

## The running example: Survey Manager

Throughout the course, a single application — **Survey Manager** — is used as the running example for demonstrating AI-assisted coding practices (code review, small feature work, unit testing, and larger feature development). It's a [Dash](https://dash.plotly.com/) web app for creating, distributing, and analyzing surveys, with three tabs:

- **Survey Maker** — build a survey by adding questions and choosing an answer type per question (open-ended text, yes/no, checkboxes, multi-select, ranking, Likert scale, numeric scale, or a row/column matrix). Existing surveys can be reloaded for editing or deleted.
- **Survey Taker** — pick a saved survey, fill it out, and submit. Each submission is stored as a response tied to that survey.
- **Survey Analyzer** — pick a survey and see a response count, a per-question chart (bar chart, histogram, or word frequency depending on question type), and a raw data table of every response.

The source lives in `src/`, with tests in `tests/`.

### Screenshots

**Survey Maker** — editing "Sample Survey", showing several question types (open-ended text, Likert scale, yes/no, numeric scale):

![Survey Maker tab, editing a survey with several question types](docs/images/survey_maker.png)

**Survey Taker** — filling out that same survey:

![Survey Taker tab, filling out a survey](docs/images/survey_taker.png)

**Survey Analyzer** — charts and raw data for its responses:

![Survey Analyzer tab, showing per-question charts and a raw response table](docs/images/survey_analyzer.png)

### Running it

```bash
pip install -r requirements.txt
python -m src.app
```

The app serves on `http://0.0.0.0:8051` by default (see `src/app.py`).

### Architecture

Survey Manager is a single-page Dash app (one process, one `Dash` instance, three tabs) rather than three separate pages. Each tab's layout and each tab's callbacks live together in one module, and `src/app.py` wires everything to the shared `Dash` app instance and owns all `@callback` definitions.

| Module | Responsibility |
|---|---|
| `src/app.py` | Creates the `Dash` app, assembles the tabbed layout, and defines every callback (loading/saving/deleting surveys, adding/removing/re-typing questions, taking a survey, analyzing results). |
| `src/models.py` | Plain dataclasses for the domain: `Question`, `Survey`, `Response`, plus `generate_id()` for their string ids. Each has `to_dict`/`from_dict` for JSON round-tripping. |
| `src/storage.py` | File-based persistence — no database. Surveys are saved as `surveys/<survey_id>.json`; each survey's responses live under `data/responses/<survey_id>/<response_id>.json`. |
| `src/survey_maker.py` | Renders the Survey Maker tab and the per-question editor. Pure rendering — no callback logic. |
| `src/survey_taker.py` | Renders the Survey Taker tab and the answer input appropriate to each question type. Pure rendering. |
| `src/survey_analyzer.py` | Renders the Survey Analyzer tab and builds the Plotly figures (`_generate_question_chart`) for each question type. |
| `src/form_logic.py` | Small, dependency-free helper functions the callbacks in `app.py` build on (e.g. parsing a "one item per line" textarea into a list, assembling a `Question` from a form's current field values, deciding which type-specific editor section should be visible). Kept separate from `app.py` so this logic can be unit tested directly, without a running Dash server. |
| `src/constants.py` | String constants for component ids, so the same literal isn't retyped across `app.py` and the tab modules. |

**Dynamic question editing.** A survey can have any number of questions, and each question's fields (type, text, required flag, options, scale, matrix rows/columns) need their own callback wiring without knowing in advance how many questions there'll be. This is done with Dash's [pattern-matching callbacks](https://dash.plotly.com/pattern-matching-callbacks): every per-question field uses a component id shaped like `{"type": "q-text", "qid": "<question id>"}` rather than a plain string id. A question's `qid` is assigned once (when it's created or loaded from disk) and never changes, which is also what lets an edited survey keep matching its previously-collected responses (`Response.answers` is keyed by question id). Adding a question appends one new editor to the currently-rendered list rather than rebuilding it, so it never disturbs a question you're already editing; deleting one removes just that question's editor. Switching a question's type never rebuilds anything — the options/scale/matrix editor sections are always present in the DOM, and a callback just toggles which one is visible, so nothing already typed into another section is lost by switching back and forth.

**No client-side JavaScript.** All interactivity is plain Dash callbacks (Python, running server-side); there is no custom JS in `assets/` wired into the app.

## Tests

```bash
pytest
```

`pytest.ini` scopes `pytest` to the unit tests in `tests/` (see the table below) and excludes the Playwright-driven scripts, which need a live browser and aren't meant for the `pytest` runner.

| File | What it covers |
|---|---|
| `tests/test_form_logic.py` | The pure helpers in `src/form_logic.py`. |
| `tests/test_app_callbacks.py` | The Dash callback functions in `src/app.py`, called directly (bypassing the Dash server). |
| `tests/test_survey_maker_render.py`, `tests/test_survey_taker_render.py` | Rendering output of the Maker/Taker layout functions. |
| `tests/test_survey_analyzer.py` | Chart-generation logic in `src/survey_analyzer.py`. |
| `tests/test_bugfix_acceptance.py`, `tests/test_delete_survey_acceptance.py` | End-to-end Playwright scripts that start a real instance of the app and drive it through a browser. Not collected by `pytest`; run directly, e.g. `python3 tests/test_bugfix_acceptance.py`. |
| `tests/test_survey_maker.py`, `tests/test_app.py`, `tests/test_quick_check.py` | Older ad-hoc Playwright/diagnostic scripts, also run directly rather than via `pytest`. |

CI (`.github/workflows/tests.yml`) runs `pytest` — the unit-test layer only — on every push and pull request to `main`.
