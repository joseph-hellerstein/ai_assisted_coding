# Survey Manager Specification

## Overview

The Survey Manager is a Plotly Dash web application that runs both client and server on the same machine. It provides three integrated workflows for managing surveys end-to-end: building them, collecting responses, and analyzing results.

## Functionality

### 1. SurveyMaker — Build Surveys
Used by investigators to construct surveys by defining questions and their answer types.

* **Survey metadata**: Title (`#maker-title`) and description (`#maker-description`) fields at the top of the page.
* **Existing survey loading**: A dropdown (`#maker-survey-select`) lists all saved surveys on disk; selecting one populates title, description, and question editors via a single callback.
* **Dynamic question editors**: Each click of "+ Add Question" appends a new editor block to `#maker-questions-container`. The entire container is re-rendered server-side with all existing questions preserved — there are no client-side add/remove operations for individual questions.
* **Supported question types** (8 total):

  | Type | Editor UI |
  |------|-----------|
  | `checkbox` / `multiselect` | Options list + "+ Add Option" button; each option has an ✕ delete button |
  | `likert` | Min/max scale inputs + label fields for min/max endpoints |
  | `yesno` | Fixed Yes/No radio items (read-only in editor) |
  | `numeric_scale` | Scale range and labels, similar to Likert |
  | `text` | Open-ended textarea answer (read-only in editor) |
  | `ranking` | Options list + "+ Add Option" button |
  | `matrix` | Separate row and column editors with ✕ delete buttons for each |

* **Required toggle**: Each question has a "Required" checkbox (`dcc.Checklist`) that is persisted as part of the question state.
* **Save**: The "💾 Save Survey" callback validates that the title is non-empty, then writes the survey JSON to `surveys/{survey_id}.json` and shows a green confirmation message.

### 2. SurveyTaker — Collect Responses
Used by participants to fill out a previously built survey.

* **Survey selection**: A dropdown (`#taker-survey-select`) populated when the tab becomes active (via a callback triggered on `main-tabs.value`).
* **Dynamic form rendering**: For each question in the loaded survey, `_render_question_input()` produces an appropriate Dash component:
  * `yesno` → `dcc.RadioItems` (Yes / No)
  * `checkbox` / `multiselect` → `dcc.Checklist` (inline)
  * `likert` / numeric_scale → `dcc.RadioItems` for Likert; `dcc.Slider` for numeric scale with step=1 and labeled marks
  * `ranking` → `dcc.Dropdown(multi=True)`
  * `matrix` → HTML `<table>` with `RadioItems` per cell (one row × column grid)
  * `text` → `dcc.Textarea`
* **Submission**: The "Submit Survey" button triggers a single callback that gathers all answers keyed by question ID, constructs a `Response` dataclass instance, and persists it to `data/responses/{survey_id}/{response_id}.json`.
* **Thank-you screen**: After submission the form is hidden (`display: none`) and a green confirmation message is shown.

### 3. SurveyAnalyzer — Generate Reports
Used by investigators to view aggregated results for any survey.

* **Survey selection**: A dropdown (`#analyzer-survey-select`), populated on tab activation, mirroring the Taker flow.
* **Response summary**: Shows survey title and response count.
* **Per-question charts** (via Plotly):
  * `yesno`, `likert` → bar chart of answer counts
  * `checkbox`, `multiselect`, `ranking` → bar chart counting option selections across all responses
  * `numeric_scale` → histogram with bin range constrained to the question's scale
  * `matrix` → one bar chart per row (rows are reordered by column order)
  * `text` → word-frequency bar chart (top 15 words, first 20 words per answer)


## Architecture

```
src/
├── app.py                    # Dash app factory + all @callback definitions
├── survey_maker.py           # Layout builder + render_question_editor()
├── survey_taker.py           # Layout builder + _render_question_input()
├── survey_analyzer.py        # Layout builder + chart generation helpers
├── models.py                 # Question, Survey, Response dataclasses
└── storage.py                # JSON file persistence (surveys/, data/responses/)
```

### Tab system
The app uses a single `dcc.Tabs(id="main-tabs")` containing three `dcc.Tab` children. Each tab loads its layout via the module-level `survey_maker_layout()`, `survey_taker_layout()`, or `survey_analyzer_layout()` functions. Tabs are switched by clicking on the tab label; the selector for Playwright is `#main-tabs > div.tab >> text=Tab Name`.

### Data flow
```
User action (button click / dropdown change)
    → Dash callback fires on server
    → Callback reads state from JSON files via storage helpers
    → Callback returns new component tree or data to Output/State props
    → Dash client re-renders the affected components
```

### State management: hidden `html.Div` instead of `dcc.Store`
The application stores transient question-state data (the list of currently-built questions) in a hidden div rather than a `dcc.Store` component. This was chosen because **Dash 4.x contains a rendering bug where `dcc.Store` fails to look up its internal Switch mapping**, producing the error `"Module 'dash.dcc' has no attribute 'Switch'"`. The workaround is:

```python
html.Div(id="maker-survey-data", children=json.dumps([]), style={"display": "none"})
```

Data flows through `Output("...", "children")` and `State("...", "children")`. Since the value is stored as textContent, callbacks must use `json.loads()` when reading via State and `json.dumps()` when returning via Output. A dedicated callback (`handle_survey_load_or_add`) uses `dash.callback_context.triggered` to determine whether the trigger was a dropdown selection (load existing survey) or an "Add Question" click (append new question editor).

### Callbacks defined in app.py
All `@callback` decorators are registered in `app.py`, even though they conceptually belong to one sub-module. This avoids **duplicate callback registration errors** when both the layout module and the callback module import each other — Dash would otherwise attempt to register the same output/input pairs twice (once from each import).

### Storage
Surveys and responses are persisted as JSON files:
* `surveys/{survey_id}.json` — full survey definition
* `data/responses/{survey_id}/{response_id}.json` — one file per response, grouped by survey

The directory structure is created lazily via `ensure_dirs()` in the storage helpers. Each ID is a timestamp-based unique string with an optional prefix (e.g., `"q_20260805221430123456"`).


## Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Hidden `html.Div` for state** instead of `dcc.Store` | Dash 4.x renderer bug with Store's internal Switch lookup; produces "Module 'dash.dcc' has no attribute 'Switch'" error |
| **Server-side re-rendering of question editors** instead of client-side DOM manipulation | Simpler callback logic; Dash handles the full diff; avoids sync issues between client and server state |
| **Single unified callback for add/load** using `callback_context` | Reduces the number of independent callbacks that compete for the same Outputs, preventing race conditions where an "Add Question" click conflicts with a dropdown change |
| **All callbacks in `app.py`** rather than per-module files | Prevents Dash from registering duplicate callback mappings when modules are imported by both layout and callback code |
| **JSON file storage** instead of a database | Zero configuration; trivial to inspect/debug; sufficient for a single-machine tool |
| **Dataclass models with `to_dict()`/`from_dict()`** | Clean serialization round-trip through JSON without custom encoders |
| **`dcc.Checklist` instead of `dcc.Switch`** for required toggle | Dash 4.x does not ship a Switch component; Checklist with a single option provides equivalent UX (checked = required) |
| **Inline question editors in the maker tab** (not collapsible accordions) | Keeps all questions visible for quick review; avoids additional UI state management for collapsed/expanded rows |

### Python compatibility
All source files use `from __future__ import annotations` to enable PEP 604 union syntax (`Question \| None`, `list[str]`) on **Python 3.9**, which is the runtime version of the Dash server environment. Without this import, these type hints would fail at module load time because Python 3.9 evaluates them eagerly.

## Testing Notes (Playwright)
The application was verified end-to-end with Playwright automation:
* Tab rendering and switching confirmed across all three tabs (`Survey Maker`, `Survey Taker`, `Survey Analyzer`).
* "Add Question" callback fires correctly; child count in `#maker-questions-container` increments from 0 → 1 → 2 with zero console errors.
* Data persists between clicks (adding a second question includes the first).
* Save validation returns expected error ("⚠️ Please enter a survey title") when title is empty.
* Tab switching triggers dropdown refresh callbacks that populate `#taker-survey-select` and `#analyzer-survey-select`.
* No JavaScript errors or page-level errors observed during testing.

### Playwright interaction notes
Dash inputs (`dcc.Input`, `dcc.Textarea`) require JS event dispatching for programmatic value changes — `.fill()`/`.type()` alone do not trigger Dash callbacks:
```javascript
const el = document.querySelector('#maker-title input');
Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(el, 'Test Survey');
el.dispatchEvent(new Event('input', {bubbles: true}));
el.dispatchEvent(new Event('change', {bubbles: true}));
```

The correct tab selector is `#main-tabs > div.tab >> text=Tab Name` — generic `text=` selectors do not match Dash's rendered tab labels.
