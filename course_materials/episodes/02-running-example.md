# Episode 2: Running Example

**Duration:** ~60 minutes
**Learning objective covered:** Use AI to understand the structure of an application — (a) how control flow relates to GUI interactions, (b) key data structures, (c) accessing and manipulating application data.
**Prerequisites:** Students have Dash installed and have already written a one-page "Hello World" Dash app (pre-course requirement). They have read `course_materials/dash_programming.md` before class.
**Materials:** The Survey Manager starter repo (`src/app.py`, `models.py`, `storage.py`, `survey_maker.py`, `survey_taker.py`, `survey_analyzer.py`, `form_logic.py`, `constants.py`), `docs/data-model.md` (kept hidden from students until the check-your-work step in 2.6), `course_materials/specifications/task_status_hovers.md`.

By the end of this episode, students will have (1) traced one GUI interaction all the way to stored data, (2) produced their own diagram of the app's data model and checked it against the real one, (3) written a short script that reads survey data directly, and (4) shipped one small, real feature (the Survey Maker hover) using that understanding.

Everything in this episode is **exploration and one small build**, not a feature of real scope — that's episodes 5 onward. The point here is to leave with an accurate mental model of the codebase before changing it.

---

## 2.1 Description of the Survey Manager (5 min)

Walk through the three tabs live (don't just describe them) — Survey Maker, Survey Taker, Survey Analyzer — using `README.md`'s screenshots or the running app. Ask students to notice, without reading code yet: what data must exist for each tab to work? (A survey definition; a submitted response; a partial response.) This primes 2.6 — they'll check their guess against the AI's answer later.

## 2.2–2.4 Dash, widgets, HTML, layout (10 min)

This is review, not new material — students read `dash_programming.md` and already built a Hello World app. Spend this block on:

- A 5-minute live walkthrough of `src/app.py`'s `app.layout` tree, pointing out the three tab buttons and their content `html.Div`s, and the "widget namespace" idea (every id is how Python code and the browser DOM refer to the same thing).
- One quick comprehension check: "Find the `id` of the Survey Title input box in `survey_maker.py`. What would you pass as `Output("maker-title", ...)` if you wanted to write to it?" (Answer: `Output("maker-title", "value")`.)

Don't over-invest here — if the room is solid on Hello World, move faster.

## 2.5 Callbacks, and (a) control flow ↔ GUI interactions (15 min)

**Concept (5 min):** Review `Input`/`Output`/`State` from `dash_programming.md` directly against a real callback — `save_survey_callback` in `app.py` is a good pick: multiple `State`s (the live form), one `Input` (the Save button), several `Output`s (status message, dropdown options, tab hover).

**Activity (10 min) — AI-assisted trace, then verify by running it:**

Each student picks one interaction (assign different ones around the room so answers can be compared):

- Clicking "Save Survey" in Survey Maker
- Clicking "Submit Survey" in Survey Taker
- Switching from Survey Maker to Survey Taker (same tab clicked twice)

**Prompt to give the AI** (adapt the bracketed interaction):

> I'm learning this codebase. When I [click "Save Survey" in the Survey Maker tab], trace exactly what happens: which `@callback` in `src/app.py` fires, what its `Input`/`State`/`Output`s are, and which helper functions in `form_logic.py` or `storage.py` it calls before anything is written to disk. List the steps in order; don't skip any.

**Then verify, don't just trust it:** run the app, perform the real interaction, and check the AI's trace step by step. Two places this app will catch a lazy trace:

- A callback's multiple `Output`s are applied in **declaration order** — a later one can silently overwrite an earlier one targeting a nested element. (`save_draft_callback`'s docstring in `app.py` explains a real case of this.)
- A dynamically-recreated component's callback can fire once at `n_clicks=0` the moment it mounts, before any real click — `submit_survey_response`'s `if not n_clicks` guard exists because of this.

If the AI's trace doesn't mention these where relevant, that's the teaching moment: **an AI's architectural explanation is a hypothesis to test by running the code, not a fact to relay.**

**Deliverable:** a short sequence diagram (mermaid, or even a numbered list) of the chosen interaction, annotated with any place the live behavior differed from the AI's first answer.

## 2.6 Information model — (b) key data structures and (c) accessing/manipulating data (20 min)

**(b) Key data structures (12 min).**

**Prompt:**

> Looking at `src/models.py` and the functions in `src/storage.py`, diagram the relationship between `Survey`, `Question`, `Response`, and `Draft`. Show which fields exist on each, and how `survey_id` connects a `Response`/`Draft` back to its `Survey`. Then explain: why isn't `Question` stored in its own file the way `Survey` is?

Students produce their own diagram first (5 min), *then* compare it against `docs/data-model.md` (6 min, now revealed) — which the instructor built the same way. Discuss any mismatch as a group: a common one is missing that a `Question`'s id is a foreign key used inside `answers`, not just inside its own `Survey`, or missing that a matrix question's answer is split across several `answers` entries keyed `f"{question_id}_matrix_{row}"` rather than one entry. These are exactly the kind of detail an AI can get wrong on a first pass if not asked to check the actual storage code, not just the dataclass.

**(c) Accessing and manipulating data (8 min).**

**Prompt:**

> Using only the public functions in `src/storage.py` (no Dash, no UI), write a short script that lists every survey with more than N responses, printing each response's `respondent_id` and `submitted_at`. Run it against the sample data in `surveys/` and `data/`.

Students run the script against the app's real on-disk data and confirm the output matches what they see in the Survey Analyzer tab for the same survey. This is their first time touching the data layer directly instead of through the UI — it matters again in episode 4, when they write unit tests against `storage.py` without a running Dash server.

**Deliverable:** the diagram from (b), plus the working script and its output from (c).

## 2.7 (A1) Hands-on: the Survey Maker hover (10 min)

Spec: `course_materials/specifications/task_status_hovers.md` — Survey Maker's landing text box should show, on hover, the list of available surveys.

1. In the starter `app.py`, find and uncomment the block marked `#A1#`.
2. Set the `title` attribute on the Survey Maker tab's text box to a string listing the available surveys (one line per survey, built from `list_surveys()`).

**Prompt:**

> I want to add a native browser tooltip to the element with id `maker-tab` in `src/app.py`, showing one line per survey from `list_surveys()`. Where does `title` go, and does it need to update when a survey is added, or only once at startup?

This last question matters: a `title` set once at import time goes stale the moment a survey is added. Have students hover, add a survey in another tab, and hover again — if it didn't update, ask the AI why, and what `Input` would need to drive it instead. This closes the loop: the same control-flow-to-GUI understanding from 2.5 is what explains why a static string isn't enough here.

**Deliverable:** a working hover on the Survey Maker tab that reflects the current list of surveys, committed to their own fork of the repo.

---

## Wrap-up check (last 5 min, informal)

Ask the room, cold: "If I added a new question type tomorrow, which three files would you expect to touch, and why?" A good answer references `models.py` (the `Question` dataclass), `form_logic.py` (assembling/validating it), and one of `survey_maker.py`/`survey_taker.py`/`survey_analyzer.py` (rendering it) — without needing to re-read the code to say so. That's the actual signal this episode worked.
