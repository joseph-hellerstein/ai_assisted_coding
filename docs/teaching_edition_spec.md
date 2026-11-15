# Survey Manager: Teaching Edition Specification

**Status:** v1.1 (2026-11-14). The code is implemented in `teaching/` and meets
acceptance criteria 1–5. Criterion 6 is still open: the course episodes and the
teaching-edition data-model diagram haven't been updated yet. All decisions are listed
in [Decisions](#11-decisions).

| Version | Change |
|---|---|
| v0.1 | First draft |
| v0.2 | Decided where the teaching edition lives: a `teaching/` folder (Q1) |
| v0.3 | Decided: question types are `text`, `yesno`, `checkbox` (no `likert`) (Q2); no "required" flag (Q3); the Survey Maker uses a form editor, not a text format |
| v0.4 | Decided: the editor has a fixed number of question rows (Q12); the form keeps its contents after a successful save (Q13) |
| v1.0 | Decided: duplicate titles are allowed (Q4); no compatibility with full-edition files (Q6); under 800 lines in `src/` (Q9); students may see the full edition for now (Q11). Spec agreed |
| v1.1 | Decided during implementation: callback 4 needs no `n_clicks` guard (Q8) |

## 1. Purpose

The full Survey Manager (`docs/survey_manager.md`) has 26 Dash callbacks across about
1,100 lines of `src/app.py`. That's too much for students to understand in the time
the course allows.

The **teaching edition** is a smaller version of the same app. It keeps the core flow
(make a survey, take it, analyze the responses) and gets there with **5 callbacks**.
Students learn on the teaching edition. The full edition stays as the instructor's
reference and as the source for the exercises.

Features removed from the teaching edition aren't lost: several become the features
students build in later episodes (see [section 9](#9-removed-features-become-exercises)).

## 2. Goals and non-goals

**Goals**

1. Each of the 5 callbacks can be explained in a few minutes, and a student can name
   all five from memory after Episode 2.
2. Each callback teaches one web-programming idea (learning objective 1): an event
   with `Input`/`State`, refreshing on navigation, building part of the page,
   collecting a variable number of answers, and rendering charts.
3. An AI assistant can be given all of `src/` as context without it being too large
   to reason about. **Target: under 800 lines in `src/` in total** (Q9).
4. The code is straightforward: no workarounds for Dash quirks unless a workaround is
   itself something we want to teach.
5. Module names and the names of key functions match the full edition, so existing
   course materials (for example, the Episode 3 starter) still apply.

**Non-goals**

- Feature parity with the full edition.
- Reading surveys or responses saved by the full edition (Q6). The two editions keep
  their data in separate folders (section 10).
- Polished styling.

## 3. Scope

### Kept

| Area | What stays |
|---|---|
| Navigation | Three tabs: Survey Maker, Survey Taker, Survey Analyzer |
| Survey Maker | Create a new survey with a form: a title, a description, and a fixed number of question rows (section 5) |
| Survey Taker | Pick a survey, enter a 5-digit respondent ID, answer the questions, submit |
| Survey Analyzer | Pick a survey; see the response count, one chart per question, and a table of raw responses |
| Question types | 3 of the full edition's 8: `text`, `yesno`, `checkbox` |
| Storage | The same file layout as the full edition, relative to `teaching/`: `surveys/<survey_id>.json` and `data/responses/<survey_id>/<response_id>.json` |

### Removed

| Removed | Why |
|---|---|
| Custom tab buttons and the active-tab store (`toggle_active_tab`, `render_active_tab`) | Dash's built-in `dcc.Tabs` does this with no callbacks |
| The six per-tab refresh callbacks | Replaced by one callback, `refresh_survey_lists` |
| Tab hover tooltips, and the inline CSS that supports them | Becomes the Episode 2 hands-on exercise |
| The **🧪 Test** panel (3 callbacks) | Developer tooling. Replaced by `scripts/make_sample_data.py` |
| Adding, deleting and re-typing questions in the editor (3 callbacks, 2 of them pattern-matching) | Replaced by a fixed number of question rows, which need no callbacks. Adding questions and showing or hiding the options field become exercises |
| Loading and editing an existing survey | Keeps the Maker to one callback. Possible exercise |
| Deleting a survey (with confirmation) | Becomes the Episode 5 small feature |
| Drafts (save, resume, delete) | Becomes the Episodes 6–7 large feature |
| Deleting a response row in the Analyzer | Not needed for teaching |
| Question types `likert`, `multiselect`, `ranking`, `numeric_scale`, `matrix` | `matrix` needs composite answer keys. The others duplicate concepts already covered by the three kept types |
| The "required" flag on questions | All questions are optional |
| Prefilling a random respondent ID | Removes the random-collision problem. The respondent types their own ID |
| The "Take Another Survey" button | Choosing another survey in the dropdown already resets the form |

## 4. Functional requirements

### 4.1 Survey Maker

- **M1.** The tab shows a title field, a description field, a fixed number of
  question rows (5, set by `N_QUESTION_ROWS` in `src/constants.py`), a
  **Save Survey** button, and a status line. Each row is laid out as in
  [section 5](#5-question-editor).
- **M2.** Clicking **Save Survey** reads the whole form and applies the rules in
  [section 5](#5-question-editor).
  - If the title is empty, every row is blank, or any row breaks a rule, the status
    line shows an orange warning and nothing is saved. A row warning names the row
    and the problem, for example:
    `⚠️ Question 3: a checkbox question needs at least 2 options.`
  - Otherwise the survey is saved with a new id, and the status line shows a green
    confirmation that includes the survey's title.
- **M3.** After a successful save, the form keeps its contents, so a similar survey
  can be made by editing and saving again. Saving again always creates a new survey
  with a new id (see M4).
- **M4.** Saving never changes or overwrites an existing survey. A title that matches
  an existing survey is allowed (Q4): both surveys are kept, and both appear in the
  dropdowns. For example, clicking **Save Survey** twice without changing anything
  creates two surveys with the same title.

### 4.2 Survey Taker

- **T1.** The tab shows a dropdown of saved surveys, sorted by title.
- **T2.** Choosing a survey shows its form: the title, the description, a respondent
  ID field, one input per question, a **Submit** button, and a status line.
  Choosing a different survey replaces the form. Clearing the dropdown removes it.
- **T3.** Inputs by question type:

  | Type | Input |
  |---|---|
  | `text` | Text area |
  | `yesno` | Yes / No radio buttons |
  | `checkbox` | One checkbox per option |

- **T4.** Clicking **Submit**:
  - If the respondent ID isn't exactly 5 digits, the status line shows
    `⚠️ Your ID must be exactly 5 digits.` The form stays as it is so the ID can be
    corrected, and nothing is saved.
  - Otherwise a `Response` is saved, the status line shows
    `✅ Thank you! Your response has been recorded.`, and the **Submit** button is
    disabled so the same answers can't be submitted twice.
- **T5.** Every rejection message must be visible on screen. (In the full edition, a
  separate callback used to hide rejection messages behind the thank-you screen.
  The teaching edition avoids that by having one callback own the outcome.)

### 4.3 Survey Analyzer

- **A1.** The tab shows a dropdown of saved surveys, sorted by title.
- **A2.** Choosing a survey shows:
  - the number of responses;
  - one chart per question:

    | Type | Chart |
    |---|---|
    | `yesno` | Bar chart of Yes/No counts, including a value with 0 responses |
    | `checkbox` | Bar chart of how many responses selected each option |
    | `text` | Bar chart of the 15 most frequent words |

  - a table with one row per response: respondent ID, submission time, and one
    column per question.
- **A3.** A survey with no responses shows "No responses yet" instead of charts and a
  table.

### 4.4 Navigation and freshness

- **N1.** Switching tabs refreshes the survey dropdowns on the Taker and Analyzer
  tabs, so a survey saved on the Maker tab appears there without restarting the app.
- **N2.** Data saved by one tab is visible on another after a tab switch.
  Updating it instantly, without a tab switch, isn't required.

## 5. Question editor

The Maker shows a fixed number of question rows (`N_QUESTION_ROWS`, 5). Every row is
always present, and nothing in the editor is added, removed or hidden by a callback.
That is what keeps the Maker down to one callback. Changing the number of rows means
changing the constant, not the code.

Each row has:

| Field | Component | Notes |
|---|---|---|
| Type | Dropdown: `text`, `yesno`, `checkbox` | Defaults to `text` |
| Question | Text input | Placeholder: "Question text (leave blank to skip)" |
| Options | Text area | Placeholder: "Options, one per line (checkbox only)". Always visible |

Each field has a pattern-matching id with the row number, for example
`{"type": "maker-q-text", "row": 2}`. That way `save_survey_callback` can read every
row with one `State(..., ALL)` per field, as `submit_survey_response` does for answers.

Rules applied on **Save Survey**:

- A row with blank question text is **skipped**, whatever its other fields say. This
  lets a survey have fewer than 5 questions.
- A `checkbox` row needs **at least 2 options**. Options are one per line. Blank lines
  and spaces at the start and end of each line are ignored.
- A `text` or `yesno` row **ignores** its options field. Nothing typed there is saved.
- Questions are saved in row order, skipping blank rows. Each saved question gets a
  new id.
- At least one row must have question text.

The rules live in a pure function in `src/form_logic.py`:

```python
assemble_questions_from_state(types, texts, options_texts) -> (questions, errors)
```

It takes three parallel lists (one entry per row) and returns the questions to save,
or a list of `"Question N: …"` error messages. It doesn't depend on Dash or on files,
so it's the main unit-testing target for Episode 4. The name matches the full
edition's function that does the same job.

## 6. Data model

| Class | Fields |
|---|---|
| `Survey` | `id`, `title`, `description`, `questions: list[Question]` |
| `Question` | `id`, `type` (`text`, `yesno` or `checkbox`), `text`, `options: list[str]` (empty unless `checkbox`) |
| `Response` | `id` (internal, e.g. `resp_482913`), `survey_id`, `respondent_id` (the 5 digits typed in), `submitted_at`, `answers: dict[question id → answer]` |

- Answers are stored as: `text` → a string, `yesno` → `"Yes"` or `"No"`,
  `checkbox` → a list of the selected options. An unanswered question is left out of
  `answers`.
- `Draft` is removed. It returns as part of the Episodes 6–7 large feature.
- Each class keeps `to_dict` / `from_dict` for JSON.
- `Response.id` and `Response.respondent_id` stay separate fields, with the same
  names as in the full edition. Mixing them up is the planted bug in the Episode 3
  code review, so that exercise still works.
- `docs/data-model-overview.md` gets a teaching-edition version with three boxes
  (no `DRAFT`).

## 7. Architecture

The same module layout as the full edition, minus what's no longer needed. All paths
below are relative to `teaching/` (see [section 10](#10-where-it-lives)).

| Module | Responsibility |
|---|---|
| `src/app.py` | Creates the app, builds the tabbed layout, defines the 5 callbacks |
| `src/models.py` | `Survey`, `Question`, `Response`, `generate_id()` |
| `src/storage.py` | `save_survey`, `load_survey`, `list_surveys`, `save_response`, `load_responses` |
| `src/form_logic.py` | Pure helpers: `assemble_questions_from_state`, `is_valid_respondent_id`, `build_response_answers` |
| `src/survey_maker.py` | Renders the Maker tab, including the question rows |
| `src/survey_taker.py` | Renders the Taker form for one survey |
| `src/survey_analyzer.py` | Builds the charts and the response table |
| `src/constants.py` | Component ids, and the number of question rows |
| `scripts/make_sample_data.py` | Writes a few sample surveys and responses (replaces the 🧪 Test panel) |

### 7.1 The five callbacks

| # | Callback | Input | State | Output(s) | Teaches |
|---|---|---|---|---|---|
| 1 | `save_survey_callback` | Save button `n_clicks` | title, description, and every row's type, text and options (pattern-matching `ALL`) | Maker status | An event with `Input` + `State`, validation, writing to storage |
| 2 | `refresh_survey_lists` | `dcc.Tabs` `value` | none | Taker dropdown options, Analyzer dropdown options | Updating on navigation; one callback with several outputs |
| 3 | `show_survey` | Taker dropdown `value` | none | Taker form container `children` | A callback that builds part of the page |
| 4 | `submit_survey_response` | Submit `n_clicks` | survey id, respondent ID, every answer (pattern-matching `ALL`) | Taker status `children`, Submit `disabled` | Collecting a variable number of answers; one callback owning the outcome |
| 5 | `analyze_survey` | Analyzer dropdown `value` | none | Analyzer results container `children` | Turning stored data into charts and a table |

Callback names 1, 3, 4 and 5 match the full edition.

### 7.2 Design rules

- **One writer per property.** No `allow_duplicate=True` anywhere. Each component
  property is written by exactly one callback.
- **Pattern matching for reading only.** Callbacks 1 and 4 read many fields with
  `ALL`. Students meet the same idea twice: once for a fixed number of rows (Maker)
  and once for a survey-dependent number of answers (Taker). No `MATCH`, and no
  pattern-matching `Output`.
- **No callback chains.** No callback's output is another callback's input.
- **`prevent_initial_call=True`** on callbacks 1 and 4 (button clicks). Callback 4
  has no `if not n_clicks` guard (Q8): the end-to-end check shows that showing the
  form, which creates the Submit button, doesn't run callback 4. That check
  (`tests/e2e_check.py`, step 2) guards against it changing.
- **No custom JavaScript or inline CSS**, beyond plain `style=` dicts.

## 8. Testing and acceptance criteria

The teaching edition is done when:

1. `src/app.py` defines exactly 5 `@callback` functions, and none uses
   `allow_duplicate` or `MATCH`.
2. `src/` has fewer than 800 lines in total (Q9).
3. `pytest` passes, with unit tests for:
   - `assemble_questions_from_state`: each question type, skipped blank rows, options
     ignored for `text`/`yesno`, every error in [section 5](#5-question-editor), and
     an all-blank form;
   - `is_valid_respondent_id` and `build_response_answers`;
   - each callback called directly with storage functions stubbed, following
     `tests/test_app_callbacks.py`;
   - chart generation for each of the 3 question types, including a survey with no
     responses.
4. A Playwright end-to-end script creates a survey with all 3 question types and one
   blank row, submits one rejected response (a bad ID) and one accepted response, and
   checks:
   - the saved survey has 3 questions, in row order;
   - the rejection message is visible and nothing was saved;
   - the accepted response is saved and Submit is disabled;
   - the Analyzer shows a count of 1, 3 charts, and a 1-row table.
5. `cd teaching && pytest` passes, the root `pytest` still passes unchanged, and CI
   runs both.
6. `teaching/README.md` describes the teaching edition. The root `README.md` points
   to it. The course episodes that refer to removed code are updated (see section 9).

## 9. Removed features become exercises

| Episode | Exercise | Built on |
|---|---|---|
| 2 | Tab hovers (A1): add a hover listing the surveys | `refresh_survey_lists`, `list_surveys` |
| 3 | Code review of the flawed duplicate-ID check | `submit_survey_response`, `Response.respondent_id`, `load_responses` |
| 4 | Unit tests | `assemble_questions_from_state` (replaces `get_draft_info`, which goes away with drafts) |
| 5 | Small feature: the duplicate-ID check, then deleting a survey with confirmation | Callback 4; a new callback with `dcc.ConfirmDialog` |
| 5 (alternatives) | Small feature: show the Options field only for `checkbox` rows | A first `MATCH` callback, like the full edition's `toggle_type_fields` |
| 6–7 | Large feature, built from a specification: drafts (save, resume, delete) | Touches `models.py`, `storage.py`, `survey_taker.py` and new callbacks |
| 6–7 (alternative) | Large feature: an "Add question" button and loading an existing survey for editing | Pattern-matching `Output`s, and appending to a list of components |

Course materials that need edits:

- **Episode 2 (`02-running-example.md`):** it mentions `save_draft_callback`, the
  mount quirk and the `#A1#` uncomment step. Its walkthrough of `save_survey_callback`
  still works, with fewer `State`s.
- **Episode 3 (`03-code-review.md`):** it describes `show_thank_you` and the
  thank-you screen bug, which don't exist in the teaching edition. Section 3.4 needs
  a new "run it" finding.
- **Course outline:** Episode 4's `get_draft_info` target.

## 10. Where it lives

**Decided (Q1):** the teaching edition lives in a `teaching/` folder in this repo,
next to the full edition, on the same branch.

`teaching/` is a self-contained project with the same layout as the repo root:

```
teaching/
├── README.md               how to run and test the teaching edition
├── pytest.ini              scopes pytest to teaching/tests
├── requirements.txt
├── .vscode/settings.json   so Pylance resolves `src.` imports when teaching/ is opened
├── src/                    the 5-callback app (section 7)
├── tests/                  unit tests and the Playwright end-to-end script
├── scripts/
│   └── make_sample_data.py
├── surveys/                created at runtime, not committed
└── data/responses/         created at runtime, not committed
```

Consequences:

- **Students work from inside `teaching/`.** They run the app with
  `cd teaching && python -m src.app` and open `teaching/` (not the repo root) as the
  VSCode folder. Inside `teaching/`, paths like `src/app.py` match what the episodes
  already say, and the `src.` import style matches the full edition.
- **Separate data.** `storage.py` resolves paths relative to `teaching/`, so the
  teaching edition reads and writes `teaching/surveys/` and `teaching/data/`, never
  the full edition's files. Both runtime folders are added to `.gitignore`.
- **Different port.** The teaching edition serves on port **8052** (the full edition
  uses 8051), so both can run at the same time for side-by-side comparison.
- **Tests run separately.** The root `pytest.ini` keeps testing only the full
  edition. `cd teaching && pytest` runs the teaching edition's tests. CI
  (`.github/workflows/tests.yml`) gets a second step that runs the teaching tests.
- **Students see both editions** when they clone the repo. The course tells them to
  stay inside `teaching/`, and the full edition is there to compare against. This is
  accepted for now (Q11). Before the course runs, revisit whether the full edition
  should move under an `instructor/` or `reference/` folder.

## 11. Decisions

| # | Question | Decision |
|---|---|---|
| Q1 | Where does the teaching edition live? | **Decided:** a `teaching/` folder in this repo (section 10) |
| Q2 | Which question types are kept? | **Decided:** `text`, `yesno`, `checkbox` |
| Q3 | Keep the "required" flag? | **Decided:** no. All questions are optional |
| Q4 | Saving a survey whose title matches an existing one? | **Decided:** allowed. Both are kept and both appear in the dropdowns |
| Q5 | ~~Fixed or configurable Likert scale?~~ | Withdrawn: `likert` is removed |
| Q6 | Must the teaching edition read full-edition files? | **Decided:** no |
| Q7 | ~~Fold `survey_maker.py` into `app.py`?~~ | Withdrawn: the form editor keeps `survey_maker.py` as its own module |
| Q8 | Is the `n_clicks` guard still needed in callback 4? | **Decided during implementation:** no. Removed; `tests/e2e_check.py` checks that showing the form submits nothing |
| Q9 | Line target for `src/` | **Decided:** under 800 lines |
| Q10 | ~~Show an example of the text format?~~ | Withdrawn: the form editor replaces the text format |
| Q11 | Is it acceptable that students see the full edition next to `teaching/`? | **Decided:** yes for now. Revisit before the course runs |
| Q12 | How should the editor handle the number of questions? | **Decided:** a fixed number of rows (`N_QUESTION_ROWS`, 5), with no callbacks. An "Add question" button stays an optional Episodes 6–7 exercise |
| Q13 | After a successful save, keep the form's contents or clear it? | **Decided:** keep them |
