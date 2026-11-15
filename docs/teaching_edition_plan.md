# Survey Manager Teaching Edition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 5-callback "teaching edition" of Survey Manager in `teaching/`, next to the full edition, that students can understand completely.

**Architecture:** A self-contained Dash project in `teaching/` with the full edition's module layout. All page structure is static except the Taker form and the Analyzer results. Exactly 5 callbacks, each the only writer of its outputs. Pure logic lives in `form_logic.py` and `survey_analyzer.py` helpers so it can be tested without Dash.

**Tech Stack:** Python 3.11, Dash (≥ 2.9; 4.4.1 installed in `aac/`), Plotly, pytest, Playwright (end-to-end check only).

**Spec:** `docs/teaching_edition_spec.md` (v1.0). Read it alongside this plan; section numbers below refer to it.

## Global Constraints

- Everything new goes under `teaching/`. Nothing in the full edition (`src/`, `tests/`, root `pytest.ini`) changes, except: one line in the root `README.md`, one step in `.github/workflows/tests.yml`, and two lines in `.gitignore`.
- Exactly 5 `@callback` functions, all in `teaching/src/app.py`: `save_survey_callback`, `refresh_survey_lists`, `show_survey`, `submit_survey_response`, `analyze_survey`.
- No `allow_duplicate`, no `MATCH`, no pattern-matching `Output`, no callback whose output is another callback's input. `ALL` is used only in `State`s of callbacks 1 and 4.
- `teaching/src/` totals fewer than 800 lines.
- Question types are exactly `text`, `yesno`, `checkbox`. No "required" flag.
- `N_QUESTION_ROWS = 5`, defined in `teaching/src/constants.py`.
- The app serves on port **8052**, started with `cd teaching && python -m src.app`.
- Data lives in `teaching/surveys/<survey_id>.json` and `teaching/data/responses/<survey_id>/<response_id>.json`.
- One import style everywhere, in code and tests: `from src.x import y` / `import src.x`, with `teaching/` on `sys.path`. (The full edition mixes `import app` and `src.` imports. Don't copy that.)
- Exact user-facing text:
  - Taker, bad ID: `⚠️ Your ID must be exactly 5 digits.`
  - Taker, success: `✅ Thank you! Your response has been recorded.`
  - Maker, row error format: `⚠️ Question {n}: {problem}` (for example `⚠️ Question 3: a checkbox question needs at least 2 options.`)
  - Analyzer, no responses: `No responses yet`

## Review Focus

Inputs the spec implies but doesn't spell out. Each has a test in the task that owns the code.

1. **Whitespace-only input** (a title of `"   "`, row text of `"  "`) counts as blank: the title is rejected and the row is skipped. Tests in Tasks 2 and 3.
2. **A cleared respondent ID field** sends `None`, not `""`. Validation must return False, not crash, and the Taker shows the bad-ID message. Tests in Tasks 2 and 4.
3. **Duplicate checkbox options** (`"Red\nRed\nBlue"`) are collapsed to unique options, keeping their first-seen order. So `"Red\nRed"` counts as 1 option and is rejected. Test in Task 2.
4. **A survey file missing** when it's selected (deleted by hand after the dropdown was filled): the Taker and Analyzer show `⚠️ This survey no longer exists.` rather than raising. Tests in Tasks 4 and 5.
5. **Word counting for text answers** ignores case and punctuation (`"Great!"` and `"great"` count as one word). Blank answers are ignored, and a `text` question with no words shows an empty chart titled with the question, not an error. Test in Task 5.

---

## File structure

```
teaching/
├── README.md                 Task 6
├── pytest.ini                Task 1
├── conftest.py               Task 1   puts teaching/ on sys.path; tmp_storage fixture
├── requirements.txt          Task 1
├── .vscode/settings.json     Task 1
├── src/
│   ├── __init__.py           Task 1
│   ├── constants.py          Task 1   component ids, N_QUESTION_ROWS, PORT
│   ├── models.py             Task 1   Question, Survey, Response, generate_id
│   ├── storage.py            Task 1   JSON files on disk
│   ├── form_logic.py         Task 2   pure helpers
│   ├── survey_maker.py       Task 3   Maker layout
│   ├── survey_taker.py       Task 4   Taker layout + one survey's form
│   ├── survey_analyzer.py    Task 5   charts, table, results
│   └── app.py                Tasks 3–5 Dash app, layout, the 5 callbacks
├── scripts/make_sample_data.py   Task 6
└── tests/
    ├── test_models_storage.py    Task 1
    ├── test_form_logic.py        Task 2
    ├── test_maker.py             Task 3
    ├── test_taker.py             Task 4
    ├── test_analyzer.py          Task 5
    ├── test_guardrails.py        Task 6   5 callbacks, no allow_duplicate/MATCH, < 800 lines
    └── e2e_check.py              Task 6   Playwright; run directly, not collected by pytest
```

Test isolation: instead of reassigning module functions (as the full edition's tests do), callback tests use a `tmp_storage` fixture that points `src.storage.SURVEYS_DIR` and `RESPONSES_DIR` at a `tmp_path`. Storage stays real, each test is isolated, and nothing leaks between tests.

---

### Task 1: Project skeleton, models and storage

**Files:**
- Create: `teaching/pytest.ini`, `teaching/conftest.py`, `teaching/requirements.txt`, `teaching/.vscode/settings.json`, `teaching/src/__init__.py`, `teaching/src/constants.py`, `teaching/src/models.py`, `teaching/src/storage.py`
- Modify: `.gitignore` (add `teaching/surveys/` and `teaching/data/`)
- Test: `teaching/tests/test_models_storage.py`

**Interfaces:**
- Produces:
  - `src.models.Question(id: str, type: str, text: str, options: list[str] = [])` (dataclass, `default_factory=list`)
  - `src.models.Survey(id: str, title: str, description: str = "", questions: list[Question] = [])`
  - `src.models.Response(id: str, survey_id: str, submitted_at: str, respondent_id: str, answers: dict[str, Any] = {})`
  - each with `to_dict() -> dict` and `from_dict(d: dict) -> cls` (`Survey.from_dict` rebuilds its `Question`s)
  - `src.models.generate_id(prefix: str) -> str`: returns `prefix + uuid4().hex[:8]`. (The full edition's timestamp ids can collide when tests create several quickly.)
  - `src.storage`: `BASE_DIR = Path(__file__).parent.parent` (that is, `teaching/`), `SURVEYS_DIR = BASE_DIR / "surveys"`, `RESPONSES_DIR = BASE_DIR / "data" / "responses"`. Every function reads these module globals at call time, so tests can redirect them.
  - `save_survey(survey: Survey) -> None`, `load_survey(survey_id: str) -> Survey | None`, `list_surveys() -> list[dict]` (each `{"id", "title"}`, sorted by `(title.lower(), id)`), `save_response(response: Response) -> None`, `load_responses(survey_id: str) -> list[Response]` (sorted by `submitted_at`; `[]` if the folder doesn't exist). Save functions create folders as needed.
  - `src.constants`: `N_QUESTION_ROWS = 5`, `PORT = 8052`, and every component id string listed in Task 3–5 Interfaces.
  - `teaching/conftest.py`: inserts `teaching/` at the front of `sys.path`, and defines the fixture `tmp_storage(tmp_path, monkeypatch) -> Path`, which sets `src.storage.SURVEYS_DIR = tmp_path / "surveys"` and `RESPONSES_DIR = tmp_path / "responses"`.
  - `teaching/pytest.ini`: `testpaths = tests`.
  - `teaching/requirements.txt`: `dash>=2.9`, `plotly`, `pytest`. (Playwright is optional, for `e2e_check.py`, and is mentioned in the README in Task 6.)
  - `teaching/.vscode/settings.json`: `{"python.analysis.extraPaths": ["."]}`.

- [ ] **Step 1: Write the failing tests** in `teaching/tests/test_models_storage.py`:
  - `test_survey_round_trips_through_dict`: a `Survey` with one `checkbox` question with options `["A", "B"]` satisfies `Survey.from_dict(s.to_dict()) == s`.
  - `test_response_round_trips_through_dict`: the same for a `Response` with `answers={"q1": ["A"]}` and `respondent_id="12345"`.
  - `test_generate_id_has_prefix_and_is_unique`: 100 calls to `generate_id("resp_")` give 100 distinct values, all starting with `"resp_"`.
  - `test_save_and_load_survey(tmp_storage)`: `load_survey(s.id) == s`, and the file exists at `tmp_storage / "surveys" / f"{s.id}.json"`.
  - `test_load_missing_survey_returns_none(tmp_storage)`: `load_survey("nope") is None`.
  - `test_list_surveys_sorted_by_title_and_keeps_duplicate_titles(tmp_storage)`: saving titles `"b"`, `"A"`, `"b"` gives `[x["title"] for x in list_surveys()] == ["A", "b", "b"]`.
  - `test_load_responses_sorted_and_empty_when_none(tmp_storage)`: `load_responses("srv_x") == []`; after saving two responses with `submitted_at` `"2026-01-02T00:00:00"` and `"2026-01-01T00:00:00"`, they come back in date order.
- [ ] **Step 2: Run them and confirm they fail.** Run: `cd teaching && pytest tests/test_models_storage.py -v`. Expected: errors on `ModuleNotFoundError: No module named 'src.models'`.
- [ ] **Step 3: Implement** the skeleton files, `models.py` and `storage.py` per the Interfaces block. JSON is written with `json.dump(..., indent=2)`.
- [ ] **Step 4: Run the tests and confirm they pass.** Run: `cd teaching && pytest -v`. Expected: 7 passed. Then from the repo root run `pytest -q` and confirm the full edition's tests still pass, with the same count as before.
- [ ] **Step 5: Commit**

```bash
git add .gitignore teaching/pytest.ini teaching/conftest.py teaching/requirements.txt teaching/.vscode teaching/src teaching/tests/test_models_storage.py
git commit -m "teaching: skeleton, models and storage"
```

### Task 2: Pure form helpers

**Files:**
- Create: `teaching/src/form_logic.py`
- Test: `teaching/tests/test_form_logic.py`

**Interfaces:**
- Consumes: `Question`, `generate_id` (Task 1).
- Produces:
  - `assemble_questions_from_state(types: list[str | None], texts: list[str | None], options_texts: list[str | None]) -> tuple[list[Question], list[str]]`. These are parallel lists, one entry per row. It returns `(questions, [])` on success, or `([], errors)`. Each error is `f"Question {n}: {problem}"`, where `n` is the 1-based row number, and **all** errors are reported, not just the first. Rules (spec section 5 plus Review Focus 1 and 3):
    - a row whose text is `None` or whitespace-only is skipped;
    - question text is stripped;
    - type `None` is treated as `"text"`;
    - a `checkbox` row splits its options on newlines, strips each, drops blanks and drops duplicates (keeping the first occurrence). Fewer than 2 remaining gives the problem `"a checkbox question needs at least 2 options."`;
    - `text` and `yesno` rows save `options=[]`, whatever was typed;
    - if no row has text, the result is `([], ["Add at least one question."])`;
    - every saved question gets `generate_id("q_")`.
  - `is_valid_respondent_id(value: str | None) -> bool`: True only for exactly 5 ASCII digits. `None` gives False (Review Focus 2).
  - `build_response_answers(qids: list[str], values: list) -> dict[str, Any]`: maps each qid to its value, leaving out unanswered ones (`None`, `[]`, or a string that's empty after stripping). Text answers are stripped.

- [ ] **Step 1: Write the failing tests** in `teaching/tests/test_form_logic.py`:

```python
def test_assemble_skips_blank_and_whitespace_rows_and_keeps_row_order():
    qs, errors = assemble_questions_from_state(
        ["text", "yesno", "checkbox", "text", None],
        ["  Name?  ", "   ", "Colors?", None, "Why?"],
        ["", "", "Red\n\n Blue \nRed", "", "ignored"],
    )
    assert errors == []
    assert [(q.type, q.text, q.options) for q in qs] == [
        ("text", "Name?", []), ("checkbox", "Colors?", ["Red", "Blue"]), ("text", "Why?", []),
    ]
    assert len({q.id for q in qs}) == 3
```

  - `test_assemble_ignores_options_for_text_and_yesno`: a `yesno` row with options `"a\nb"` saves `options == []`.
  - `test_assemble_reports_every_bad_checkbox_row`: rows 2 and 4 are checkboxes with options `"Only one"` and `"Red\nRed"`. Expect `qs == []` and `errors == ["Question 2: a checkbox question needs at least 2 options.", "Question 4: a checkbox question needs at least 2 options."]`.
  - `test_assemble_all_blank_form`: 5 blank rows give `([], ["Add at least one question."])`.
  - `test_is_valid_respondent_id`: parametrize over `"12345"` → True, and `"1234"`, `"123456"`, `"12a45"`, `" 1234"`, `""`, `None` → False.
  - `test_build_response_answers_omits_unanswered_and_strips_text`: qids `["q1", "q2", "q3", "q4"]` with values `["  hi ", None, [], ["Red"]]` give `{"q1": "hi", "q4": ["Red"]}`.
- [ ] **Step 2: Run them and confirm they fail.** Run: `cd teaching && pytest tests/test_form_logic.py -v`. Expected: `ImportError`.
- [ ] **Step 3: Implement** the three functions per the Interfaces block.
- [ ] **Step 4: Run the tests and confirm they pass.** Run: `cd teaching && pytest -v`. Expected: all pass.
- [ ] **Step 5: Commit**

```bash
git add teaching/src/form_logic.py teaching/tests/test_form_logic.py
git commit -m "teaching: form helpers (assemble questions, validate ID, build answers)"
```

### Task 3: App shell, Survey Maker, and `save_survey_callback`

This task builds the **whole static layout** (all three tabs, with empty Taker and Analyzer containers) so that Tasks 4 and 5 only add callbacks and renderers.

**Files:**
- Create: `teaching/src/survey_maker.py`, `teaching/src/app.py`, `teaching/src/survey_taker.py` (layout function only), `teaching/src/survey_analyzer.py` (layout function only)
- Test: `teaching/tests/test_maker.py`

**Interfaces:**
- Consumes: `assemble_questions_from_state` (Task 2), `Survey`, `generate_id`, `save_survey` (Task 1).
- Produces:
  - Constants:
    - tabs: `MAIN_TABS = "main-tabs"`, with tab values `"maker"`, `"taker"`, `"analyzer"`;
    - Maker: `MAKER_TITLE = "maker-title"`, `MAKER_DESCRIPTION = "maker-description"`, `MAKER_SAVE = "maker-save"`, `MAKER_STATUS = "maker-status"`;
    - row-field types: `MAKER_Q_TYPE = "maker-q-type"`, `MAKER_Q_TEXT = "maker-q-text"`, `MAKER_Q_OPTIONS = "maker-q-options"`;
    - Taker: `TAKER_SURVEY_SELECT = "taker-survey-select"`, `TAKER_FORM = "taker-form"`;
    - Analyzer: `ANALYZER_SURVEY_SELECT = "analyzer-survey-select"`, `ANALYZER_RESULTS = "analyzer-results"`.
  - `survey_maker.maker_layout() -> html.Div`: the title `dcc.Input`, the description `dcc.Textarea`, `N_QUESTION_ROWS` rows (each with a type `dcc.Dropdown` (options `text`/`yesno`/`checkbox`, value `"text"`, `clearable=False`), a text `dcc.Input` and an options `dcc.Textarea`, with ids `{"type": MAKER_Q_TYPE, "row": i}` etc. for `i` in `range(N_QUESTION_ROWS)` and the spec's placeholders), the save button, and an empty status `html.Div`.
  - `survey_taker.taker_layout() -> html.Div`: a dropdown `TAKER_SURVEY_SELECT` plus an empty `html.Div(id=TAKER_FORM)`.
  - `survey_analyzer.analyzer_layout() -> html.Div`: a dropdown `ANALYZER_SURVEY_SELECT` plus an empty `html.Div(id=ANALYZER_RESULTS)`.
  - `app.app`: a `Dash(__name__, suppress_callback_exceptions=True, title="Survey Manager (teaching)")`. Its layout is a heading plus `dcc.Tabs(id=MAIN_TABS, value="maker")` with three `dcc.Tab`s containing the three layouts. `if __name__ == "__main__": app.run(debug=True, port=PORT)`.
  - `app.save_survey_callback(n_clicks, title, description, types, texts, options_texts) -> html.Div`: `Input(MAKER_SAVE, "n_clicks")`, `State`s in that order (the row fields via `{"type": ..., "row": ALL}`), `Output(MAKER_STATUS, "children")`, `prevent_initial_call=True`. Returns a status `html.Div`:
    - an orange `⚠️ Please enter a survey title.` for a blank or whitespace-only title;
    - otherwise, if there are errors, one orange line per error, each `⚠️ ` + the error;
    - otherwise it saves `Survey(generate_id("srv_"), title.strip(), (description or "").strip(), questions)` and returns a green `✅ Survey '{title}' saved.`

- [ ] **Step 1: Write the failing tests** in `teaching/tests/test_maker.py`. Use `str(component)` to search the returned component's text, and `list_surveys()` / `load_survey()` with `tmp_storage` to check what was saved.
  - `test_maker_layout_has_n_rows_with_pattern_ids`: collect the ids in `maker_layout()` whose `type` is `MAKER_Q_TEXT`; the `row` values are `[0, 1, 2, 3, 4]`.
  - `test_save_creates_survey_with_questions_in_row_order(tmp_storage)`: the rows are `text "Name?"`, blank, `checkbox "Colors?"` with `"Red\nBlue"`, blank, blank. The status contains `"✅"` and `"Demo"`. `list_surveys()` has 1 entry, and its loaded survey has 2 questions in that order.
  - `test_save_rejects_blank_and_whitespace_title(tmp_storage)`: parametrize the title over `""`, `"   "`, `None`. The status contains `"Please enter a survey title"`, and `list_surveys() == []`.
  - `test_save_reports_row_errors_and_saves_nothing(tmp_storage)`: a checkbox in row 3 with one option. The status contains `"Question 3: a checkbox question needs at least 2 options."`, and nothing is saved.
  - `test_save_twice_creates_two_surveys_with_same_title(tmp_storage)`: two identical calls leave `list_surveys()` with 2 entries with equal titles and different ids (spec M3/M4).
- [ ] **Step 2: Run them and confirm they fail.** Run: `cd teaching && pytest tests/test_maker.py -v`. Expected: `ImportError`.
- [ ] **Step 3: Implement** the four modules per the Interfaces block. `app.py` imports the layout functions and contains only `save_survey_callback` for now.
- [ ] **Step 4: Run the tests and confirm they pass,** then start the app. Run: `cd teaching && pytest -v`. Expected: all pass. Then run `cd teaching && python -m src.app`, open `http://127.0.0.1:8052`, save a 2-question survey, and confirm the green message appears and `teaching/surveys/` has one new JSON file. Stop the server and delete that file.
- [ ] **Step 5: Commit**

```bash
git add teaching/src teaching/tests/test_maker.py
git commit -m "teaching: app shell, Survey Maker form, save_survey_callback"
```

### Task 4: Survey Taker (`refresh_survey_lists`, `show_survey`, `submit_survey_response`)

**Files:**
- Modify: `teaching/src/survey_taker.py`, `teaching/src/app.py`, `teaching/src/constants.py`
- Test: `teaching/tests/test_taker.py`

**Interfaces:**
- Consumes: `list_surveys`, `load_survey`, `save_response` (Task 1); `is_valid_respondent_id`, `build_response_answers` (Task 2); the layout ids (Task 3).
- Produces:
  - Constants: `TAKER_RESPONDENT_ID = "taker-respondent-id"`, `TAKER_SUBMIT = "taker-submit"`, `TAKER_STATUS = "taker-status"`, `ANSWER = "answer"`.
  - `survey_taker.render_survey_form(survey: Survey) -> html.Div`, which contains:
    - the title and description;
    - `dcc.Input(id=TAKER_RESPONDENT_ID, type="text", maxLength=5, placeholder="5 digits")`, empty, with no prefill;
    - per question, a label plus an input with id `{"type": ANSWER, "qid": q.id}`: `text` → `dcc.Textarea`; `yesno` → `dcc.RadioItems(["Yes", "No"])`; `checkbox` → `dcc.Checklist(q.options)`;
    - `html.Button("Submit", id=TAKER_SUBMIT, n_clicks=0)`;
    - an empty `html.Div(id=TAKER_STATUS)`.
  - `app.refresh_survey_lists(tab) -> tuple[list[dict], list[dict]]`: `Input(MAIN_TABS, "value")`; `Output(TAKER_SURVEY_SELECT, "options")`, `Output(ANALYZER_SURVEY_SELECT, "options")`. Both outputs are `[{"label": s["title"], "value": s["id"]} for s in list_surveys()]`. No `prevent_initial_call`, so the dropdowns are filled on page load.
  - `app.show_survey(survey_id) -> list | html.Div`: `Input(TAKER_SURVEY_SELECT, "value")`; `Output(TAKER_FORM, "children")`. Returns `[]` for no selection, `render_survey_form(survey)` normally, and an orange `⚠️ This survey no longer exists.` if `load_survey` returns None (Review Focus 4).
  - `app.submit_survey_response(n_clicks, survey_id, respondent_id, values, ids) -> tuple`: `Input(TAKER_SUBMIT, "n_clicks")`; `State(TAKER_SURVEY_SELECT, "value")`, `State(TAKER_RESPONDENT_ID, "value")`, `State({"type": ANSWER, "qid": ALL}, "value")`, `State({"type": ANSWER, "qid": ALL}, "id")`; `Output(TAKER_STATUS, "children")`, `Output(TAKER_SUBMIT, "disabled")`; `prevent_initial_call=True`. Behaviour:
    - `not n_clicks` → `(no_update, no_update)` (the Q8 guard; settled in Task 6);
    - missing survey → `(orange "⚠️ This survey no longer exists.", no_update)`;
    - invalid ID → `(orange "⚠️ Your ID must be exactly 5 digits.", no_update)`;
    - otherwise it saves `Response(generate_id("resp_"), survey_id, datetime.now().isoformat(timespec="seconds"), respondent_id, build_response_answers([i["qid"] for i in ids], values))` and returns `(green "✅ Thank you! Your response has been recorded.", True)`.

- [ ] **Step 1: Write the failing tests** in `teaching/tests/test_taker.py`. Each saves a 3-question survey (one of each type) with `tmp_storage` first.
  - `test_refresh_survey_lists_fills_both_dropdowns(tmp_storage)`: both returned lists are equal and contain `{"label": <title>, "value": <id>}`.
  - `test_show_survey_renders_one_answer_input_per_question(tmp_storage)`: the rendered form contains 3 ids with `type == ANSWER`, an empty respondent ID field (`value` is None or `""`), and the Submit button.
  - `test_show_survey_with_no_selection_is_empty`: `show_survey(None) == []`.
  - `test_show_survey_for_missing_file_says_so(tmp_storage)`: the string of `show_survey("srv_gone")` contains `"no longer exists"`.
  - `test_submit_saves_response_and_disables_button(tmp_storage)`: answering only the yesno question with `"Yes"` returns a status containing `"Thank you"` and `disabled is True`. `load_responses(id)` has 1 response with `answers == {<yesno qid>: "Yes"}` and `respondent_id == "12345"`.
  - `test_submit_rejects_bad_or_cleared_id_and_keeps_button(tmp_storage)`: parametrize over `"12"`, `"abcde"`, `None`. The status contains `"Your ID must be exactly 5 digits."`, `disabled is no_update`, and nothing is saved.
  - `test_submit_for_missing_survey_saves_nothing(tmp_storage)`: `survey_id="srv_gone"` gives a status containing `"no longer exists"`, and nothing is saved.
  - `test_submit_ignores_zero_click_mount_event(tmp_storage)`: `n_clicks=0` returns `(no_update, no_update)`, and nothing is saved.
- [ ] **Step 2: Run them and confirm they fail.** Run: `cd teaching && pytest tests/test_taker.py -v`. Expected: `ImportError` / `AttributeError`.
- [ ] **Step 3: Implement** `render_survey_form` and the three callbacks per the Interfaces block.
- [ ] **Step 4: Run the tests and confirm they pass,** then check in the browser. Run: `cd teaching && pytest -v`. Expected: all pass. Then start the app, save a survey, switch to Survey Taker, submit with ID `12` (the warning shows and the form stays), then with `12345` (thank-you message, Submit disabled). Delete the test files from `teaching/surveys/` and `teaching/data/`.
- [ ] **Step 5: Commit**

```bash
git add teaching/src teaching/tests/test_taker.py
git commit -m "teaching: Survey Taker (refresh lists, show survey, submit response)"
```

### Task 5: Survey Analyzer (`analyze_survey`)

**Files:**
- Modify: `teaching/src/survey_analyzer.py`, `teaching/src/app.py`
- Test: `teaching/tests/test_analyzer.py`

**Interfaces:**
- Consumes: `load_survey`, `load_responses` (Task 1); `ANALYZER_SURVEY_SELECT`, `ANALYZER_RESULTS` (Task 3).
- Produces:
  - `word_counts(texts: list[str], top_n: int = 15) -> list[tuple[str, int]]`: lowercases, takes words matching `[a-z0-9']+`, and returns the `top_n` most common as `(word, count)`, ties broken alphabetically (Review Focus 5).
  - `question_chart(question: Question, responses: list[Response]) -> go.Figure`: a bar chart titled with the question text. Its x values and counts:
    - `yesno`: x `["Yes", "No"]`, counts include zeros;
    - `checkbox`: x `question.options` in order, counting responses whose answer list contains each option, zeros included;
    - `text`: `word_counts` of the answers (no bars if there are no words).
    Unanswered questions aren't counted.
  - `response_table(survey: Survey, responses: list[Response]) -> dash_table.DataTable`: columns `Respondent ID`, `Submitted`, then one per question (header = question text, id = question id). A checkbox answer is shown as `", ".join(...)`, and an unanswered question as `""`.
  - `build_results(survey: Survey, responses: list[Response]) -> html.Div`: `f"Responses: {len(responses)}"`, then either `No responses yet`, or one `dcc.Graph(figure=question_chart(q, responses))` per question followed by the table.
  - `app.analyze_survey(survey_id) -> list | html.Div`: `Input(ANALYZER_SURVEY_SELECT, "value")`; `Output(ANALYZER_RESULTS, "children")`. Returns `[]` for no selection, an orange `⚠️ This survey no longer exists.` when `load_survey` returns None, and otherwise `build_results(survey, load_responses(survey_id))`.

- [ ] **Step 1: Write the failing tests** in `teaching/tests/test_analyzer.py`. These build `Survey`/`Response` objects in memory; only the callback tests use `tmp_storage`.
  - `test_word_counts_ignores_case_punctuation_and_blanks`: `word_counts(["Great!", "great idea", "", "  "]) == [("great", 2), ("idea", 1)]`.
  - `test_yesno_chart_includes_zero_counts`: two `"Yes"` answers give `list(fig.data[0].x) == ["Yes", "No"]` and `list(fig.data[0].y) == [2, 0]`.
  - `test_checkbox_chart_counts_each_option_in_order`: options `["Red", "Blue", "Green"]` with answers `["Red"]`, `["Red", "Green"]` and one response without this question give y `[2, 0, 1]`.
  - `test_text_chart_with_no_words_has_no_bars`: `fig.layout.title.text == question.text`, and the trace has no x values (or there are no traces).
  - `test_response_table_rows_and_blank_cells`: two responses, one missing an answer, give 2 rows. The missing cell is `""` and the checkbox cell is `"Red, Green"`.
  - `test_build_results_without_responses_says_so`: its string contains `"Responses: 0"` and `"No responses yet"`, and it has no `Graph`.
  - `test_analyze_survey_end_to_end_through_storage(tmp_storage)`: with a 3-question survey saved plus 1 response, the string contains `"Responses: 1"`, and the result has 3 `dcc.Graph` components.
  - `test_analyze_survey_missing_file_and_no_selection(tmp_storage)`: `analyze_survey(None) == []`, and `"no longer exists"` is in `str(analyze_survey("srv_gone"))`.
- [ ] **Step 2: Run them and confirm they fail.** Run: `cd teaching && pytest tests/test_analyzer.py -v`. Expected: `ImportError`.
- [ ] **Step 3: Implement** the helpers and the callback per the Interfaces block.
- [ ] **Step 4: Run the tests and confirm they pass.** Run: `cd teaching && pytest -v`. Expected: all pass.
- [ ] **Step 5: Commit**

```bash
git add teaching/src teaching/tests/test_analyzer.py
git commit -m "teaching: Survey Analyzer (charts, table, analyze_survey)"
```

### Task 6: Guardrails, end-to-end check, sample data, docs and CI

**Files:**
- Create: `teaching/tests/test_guardrails.py`, `teaching/tests/e2e_check.py`, `teaching/scripts/make_sample_data.py`, `teaching/README.md`
- Modify: `README.md` (root), `.github/workflows/tests.yml`, and possibly `teaching/src/app.py` (Q8)

**Interfaces:**
- Consumes: everything above.
- Produces:
  - `make_sample_data.py`: run as `cd teaching && python -m scripts.make_sample_data`. It writes 2 surveys (each with all 3 question types) and 5 responses per survey, through `src.storage`.
  - `e2e_check.py`: run directly with `cd teaching && python tests/e2e_check.py`. Exit code 0 means it passed. It starts the app in a subprocess on port **8062**, after redirecting `src.storage.SURVEYS_DIR` / `RESPONSES_DIR` to a temporary folder. It does this with `python -c` and a small launcher string, so `src/` gets no test-only code. Then it drives Chromium with Playwright.

- [ ] **Step 1: Write the guardrail tests** in `teaching/tests/test_guardrails.py` (spec section 8, items 1–2):
  - `test_exactly_five_callbacks`: `Path("src/app.py").read_text().count("@callback(") == 5`, and the set of function names defined directly under those decorators is the 5 names in Global Constraints.
  - `test_no_allow_duplicate_or_match`: none of `"allow_duplicate"`, `"MATCH"` appears in any `src/*.py`.
  - `test_src_under_800_lines`: the total line count of `src/**/*.py` is `< 800`.
- [ ] **Step 2: Run them.** Run: `cd teaching && pytest tests/test_guardrails.py -v`. Expected: 3 passed. If the line count fails, shorten the code; don't raise the limit. The limit is a spec decision (Q9).
- [ ] **Step 3: Write `e2e_check.py`** to cover spec section 8, item 4, in this order, asserting each step:
  1. On the Maker tab, fill in the title `E2E`, row 1 `text "Comments?"`, row 2 blank, row 3 `checkbox "Colors?"` with `"Red\nBlue"`, row 4 `yesno "Attended?"`, and save. The status contains `✅`.
  2. Switch to Survey Taker and choose `E2E`. The form shows 3 answer inputs.
  3. Enter ID `12` and submit. The bad-ID message is visible, Submit is enabled, and no response file exists.
  4. Enter ID `12345`, tick `Red`, choose `Yes`, and submit. The thank-you message is visible, Submit is disabled, and there's 1 response file.
  5. Switch to Survey Analyzer and choose `E2E`. The page shows `Responses: 1` and 3 charts (`.js-plotly-plot`), and the table has 1 data row.
- [ ] **Step 4: Run it.** Run: `cd teaching && python tests/e2e_check.py`. Expected: each step printed as OK, and exit code 0.
- [ ] **Step 5: Settle Q8.** Temporarily delete the `if not n_clicks: return no_update, no_update` guard from `submit_survey_response`, and add an e2e step that chooses a survey and waits 1.5 s. Then check that the status is still empty and no response file exists. Then:
  - **if it passes** without the guard, leave the guard out, delete `test_submit_ignores_zero_click_mount_event` (it calls the function directly with a valid ID, so without the guard it would save), and keep the new e2e step as the regression check for the real mount behaviour;
  - **if it fails,** restore the guard with a one-line comment explaining why.

  Record the outcome in the spec's Decisions table (Q8). Rerun `pytest -v` and `e2e_check.py`; both must pass.
- [ ] **Step 6: Write `make_sample_data.py`,** then run it and open the app to confirm both surveys appear in all three tabs' dropdowns, with charts in the Analyzer. Delete the generated data afterwards.
- [ ] **Step 7: Docs and CI.**
  - **`teaching/README.md`:** what the teaching edition is (link to the spec), how to run it (`cd teaching && python -m src.app`, port 8052), how to test (`pytest`; optional `pip install playwright && playwright install chromium`, then `python tests/e2e_check.py`), sample data, the 5 callbacks in a table (name, `Input`, `Output`), and "open `teaching/` as your VSCode folder."
  - **Root `README.md`:** one line under the title pointing students to `teaching/README.md`.
  - **`.github/workflows/tests.yml`:** after the existing pytest step, add a step named `Run teaching-edition unit tests` with `working-directory: teaching` and `run: pip install -r requirements.txt && pytest -v`.
- [ ] **Step 8: Final verification.** Run `cd teaching && pytest -v` (all pass), `python tests/e2e_check.py` (exit 0), and from the repo root `pytest -q` (the full edition's count is unchanged). Check `git status` to confirm nothing outside `teaching/`, `README.md`, `.gitignore`, `.github/workflows/tests.yml` and the spec's Q8 row has changed.
- [ ] **Step 9: Commit**

```bash
git add teaching README.md .github/workflows/tests.yml docs/teaching_edition_spec.md
git commit -m "teaching: guardrails, e2e check, sample data, README and CI"
```

---

## Not in this plan

- **Updating the course episodes** (spec section 9: Episode 2, Episode 3 section 3.4, and the outline's Episode 4 target). That is teaching-content work, best done together once the code exists, so the episodes can quote the real code. Spec acceptance criterion 6 isn't met until that's done.
- **The `docs/data-model-overview.md` teaching-edition diagram** (spec section 6). This goes with the episode updates above.
