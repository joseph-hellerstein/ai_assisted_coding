# Episode 3: AI-Assisted Code Review

**Duration:** ~60 minutes
**Learning objective covered:** Conduct a code review using AI assists.
**Prerequisites:** Episode 2: students can trace a GUI interaction through a callback, know the `Survey`/`Question`/`Response`/`Draft` model, and have read `storage.py` directly. They have completed the pre-course LLM basics (VSCode setup, effective prompting, tokens and context), so 3.1 is a review that applies those ideas to code review.
**Materials:** The Survey Manager repo; `course_materials/episodes/code/ep3_duplicate_id_starter.py`, with the **instructor-notes section removed** from the copy students receive; `course_materials/prompting_skills.md`; one survey with at least two responses (generate them with the app's **🧪 Test** panel).

By the end of this episode, students will have (1) reviewed a realistic AI-written change on its own `git` branch, (2) found where in the code a respondent's ID is checked and stored, (3) run an AI-assisted review and graded its findings against their own, and (4) run the app to see how it actually responds when a submission is rejected, which can't be learned from reading the diff.

The change under review is a first draft of **"check for a duplicate survey-taker ID,"** written the way an AI assistant plausibly would on a first pass. Students **review** it; they don't fix it. Episode 5 implements the same feature properly, so everything found here becomes the requirements list for that episode.

The main lesson: **a code review is only as good as the context it's given.** An AI that reviews only the diff will miss things that one given the right surrounding files will catch. Neither will catch a bug that only shows up when you run the app.

---

## Before class (instructor prep, ~10 min)

1. On the starter repo, create a branch `ep3-duplicate-id` from `main`.
2. Add `has_duplicate_respondent_id` from the starter file to `src/form_logic.py`, and add `from src.storage import load_responses` to that module's imports.
3. In `src/app.py`, import it next to `is_valid_respondent_id`. Insert the starter's duplicate-check block into `submit_survey_response` directly **after** the `if not survey_id:` check and **before** the existing `is_valid_respondent_id` check, so the order matches the excerpt. Mark both insertions with `#A2#` comments, as episode 2 did with `#A1#`.
4. Commit with the message `Reject duplicate respondent IDs on submit` and push the branch. Students check out this branch. They don't receive the instructor notes.
5. Run `pytest` on the branch and confirm it still passes. Nothing tests the new function, and that gap is a review finding in itself, picked up in episode 4.

---

## 3.1 Review of LLM basics, applied to code review (15 min)

### Prompts, tokens, context (5 min)

Students already know these terms. Spend the time on what each means **for a review**:

- **Context is everything the model can see.** A reviewer that sees only the diff doesn't know what `r.id` is. That's defined in `models.py`, which isn't in the diff. A reviewer can't flag a mistake about something it can't see.
- **Tokens make context a budget.** Show rough sizes: `src/app.py` alone is about 45,000 characters (~11,000 tokens), while `models.py` plus `storage.py` are about 2,000 tokens together. Pasting the whole repo works for this small app but not for a real one, and a large context dilutes the model's attention. The skill is choosing the **right** files: the diff plus the definitions it depends on.
- **Prompts set the reviewer's job.** Return to `prompting_skills.md` (role, context, specific request, precise references). "Review this" gets generic style comments. "Is each field this function compares the one the docstring promises?" gets the bug.

### Setup in VSCode (5 min)

Get everyone to the same working state. Ask them to raise a hand at each step if anything goes wrong.

- The AI assistant from the pre-course setup is open in VSCode and can read files in the workspace.
- The repo is cloned and the terminal is in the repo's root folder.
- `python -m src.app` starts the app at `http://localhost:8051` (or the address it prints). Leave it running for 3.5.

### `git` best practices for AI-assisted work (5 min)

- **Separate branch.** AI-written changes live on their own branch (`ep3-duplicate-id`), never directly on `main`. If the change is bad, deleting the branch undoes it.
- **Review the diff, not the files.** Run `git diff main...ep3-duplicate-id`. The three-dot form shows only what the branch changed relative to where it started. The diff is the review's subject, and the tool to hand an AI as its starting context.
- **Small, single-purpose commits.** One feature per commit makes the diff short enough to review well, whether by a human or an AI.
- **Nothing merges unreviewed.** That includes code the AI wrote. The AI that wrote it is a poor reviewer of it, because it has the same blind spots.

**Activity:** every student checks out the branch and saves the diff to a file:

```bash
git fetch origin
git switch ep3-duplicate-id
git diff main...ep3-duplicate-id > ep3.diff
```

---

## 3.2 Coding task: where in the code is the ID checked? (10 min)

**Human pass first (5 min, no AI).** Read `ep3.diff` and answer on paper:

1. When the respondent clicks **Submit Survey**, which callback runs, and in what order does it now check things?
2. `has_duplicate_respondent_id` compares `r.id`. What is `r`, and what is in its `id` field? (Students should open `models.py` to answer this. That's the point.)
3. Where does a new respondent's ID come from before they type anything?

**Then the AI-assisted trace (5 min).** Students use the same tracing technique as episode 2's 2.5:

> I'm reviewing the change in `ep3.diff`. When I click "Submit Survey" in the Survey Taker tab, trace exactly what happens: which `@callback` in `src/app.py` fires, what its `Input`/`State`/`Output`s are, and every check it makes before `save_response` writes to disk, in order. For each field the new code compares, tell me which class it belongs to in `src/models.py` and how its value is generated.

**Expected answers**, for the instructor to check against:

1. `submit_survey_response`. The checks in order are: the `n_clicks` guard, `survey_id`, then the **new** duplicate check, then the **existing** `is_valid_respondent_id`.
2. `r` is a `Response`. `r.id` is the internal id, `generate_id("resp_")`, a value like `resp_482913`. The ID the respondent types is `r.respondent_id`.
3. `generate_respondent_id()` in `form_logic.py` prefills a **random** 5-digit ID (`survey_taker.py` sets it as the field's default).

If a student's paper answer to question 2 was "the respondent's ID," don't correct them yet. That mistake is exactly what 3.3 is built to catch.

---

## 3.3 The AI-assisted review (15 min)

Run the review **twice**, with different context, and compare the results. The difference between the two runs is the lesson.

**Run A: diff only (4 min).** Students start a **fresh** AI session (so it hasn't seen the 3.2 trace), attach or paste only `ep3.diff`, and ask:

> You are a senior Python reviewer. Review this diff for correctness bugs, ranked most severe first. For each, give the line, the failure scenario, and a suggested fix.

**Run B: diff plus the definitions it depends on (4 min).** In a new session, students attach `ep3.diff`, `src/models.py`, `src/storage.py`, and `src/form_logic.py`, and ask:

> You are a senior Python reviewer. The attached diff adds duplicate-ID rejection to Survey Taker submissions. The other attached files define every type and storage function the diff uses. Review the diff for correctness bugs, ranked most severe first. For each, give the line, a concrete failure scenario (specific inputs and what goes wrong), and a suggested fix. For every field the diff compares, confirm against `models.py` that it's the field the docstring promises. List any assumptions the diff makes that a spec should settle.

**Grade the reviews (7 min).** Reveal the findings list below and have each student mark both runs as **found**, **missed**, or **wrong**. Wrong means a confident finding that isn't true. Treat that category seriously, because a reviewer that produces confident false findings wastes the developer's time.

| # | Finding | Kind | Where |
|---|---|---|---|
| 1 | Compares `r.id` (the internal `resp_…` id) instead of `r.respondent_id`. The two can never be equal, so the function **always returns `False`** and the feature does nothing. | Bug (headline) | `has_duplicate_respondent_id` |
| 2 | The duplicate check runs **before** format validation. It's harmless while bug 1 exists, but once bug 1 is fixed, a blank ID collides with every older response whose `respondent_id` is `""` (responses saved before the field existed, and **🧪 Test**-panel sample data). The user then sees "already used" instead of "must be 5 digits." Validate format first, uniqueness second. | Latent bug | Call order in `submit_survey_response` |
| 3 | The default ID is **random** (`generate_respondent_id`). Once fixed, a brand-new respondent can be rejected as a duplicate of an ID they never chose. With more responses this becomes likely, by the same birthday-problem reasoning as shared birthdays. | Design consequence | Interaction with `survey_taker.py` |
| 4 | Is uniqueness per survey (`load_responses(survey_id)`) or across all surveys? The spec doesn't say. A good review flags this as an assumption to confirm rather than picking one silently. | Design question | `has_duplicate_respondent_id` |
| 5 | No tests were added for the new function. | Process | Whole diff |

Expected pattern, which isn't guaranteed and is worth discussing either way: Run A often finds 2, 4, and 5 but misses 1, or guesses at 1 while hedging, because it has never seen `Response`. Run B usually finds 1. Finding 3 needs `survey_taker.py`, which neither run was given. Ask the room: **what would you have to attach for the AI to find 3?**

Reviews that diverge are useful. If one AI flags something the table doesn't list, have the student check it against the code before accepting or dismissing it. Possible extra findings worth crediting are a check-then-write race between two simultaneous submits and the cost of `load_responses` reading every response file on each submit. Both are real but low priority for this app.

**Deliverable:** each student's graded table (found, missed, or wrong for runs A and B), plus one sentence on what context made the difference.

---

## 3.4 How does the system respond? Run it. (10 min)

So far, everything has come from reading. Now students **use the app** to see how a rejected submission looks to a respondent. Because bug 1 makes the duplicate check a no-op, use the rejection path that does fire: the existing format check.

1. In the running app, open **Survey Taker** and choose a survey.
2. Replace the prefilled ID with `12` (too short) and click **Submit Survey**.
3. Before anyone looks closely, ask: *what should the respondent see?* (The orange "⚠️ Your ID must be exactly 5 digits." message, with the form still there to fix.)

**What actually happens:** the page shows **"✅ Thank you for your response!"** The warning is hidden and **nothing is saved**. Confirm with `ls data/responses/<survey_id>/`: no new file. The respondent believes they submitted, but nothing was recorded.

**Why** (have students ask the AI this, giving it `src/app.py` and `src/survey_taker.py`):

> When I submit the Survey Taker form with an invalid ID, `submit_survey_response` returns a warning, but the page shows the thank-you screen instead. Which callbacks fire on the Submit click, and why is the warning not visible?

Two callbacks share the same `Input` (`taker-submit.n_clicks`). `submit_survey_response` validates and writes the warning into `taker-status`. `show_thank_you` hides `taker-survey-form` and shows `taker-thankyou` on **any** click with `n_clicks > 0`, without checking whether the submission succeeded. `taker-status` is **inside** `taker-survey-form` (`survey_taker.py`), so the warning is written into a container that has just been hidden.

**Takeaways:**

- **This bug isn't in the diff.** It's in code that already exists on `main`. A review scoped to the diff, by a human or an AI, can't find it. Running the app does.
- **It decides whether the new feature is visible at all.** Even after bugs 1 and 2 are fixed, every "already used" rejection would also be hidden behind the thank-you screen, with no response saved. The feature can't work until this is fixed, so it goes at the top of episode 5's requirements list.
- This mirrors episode 2's rule: **an AI's account of the code is a hypothesis; running the app is the test.**

**Deliverable:** a short addition to the 3.3 table, labeled "found by running": what the respondent sees, what was saved, and which two callbacks cause it.

---

## Wrap-up check (last 5 min, informal)

Ask the room, cold: *"You're about to ask an AI to review a 40-line diff. What do you attach, and what do you do after it answers?"*

A good answer covers three things without prompting:

- **Attach** the diff plus the definitions it uses: the classes in `models.py` it reads fields from, and the functions it calls in `storage.py`.
- **Ask** a specific reviewer's question, such as "does each compared field match its docstring?", rather than "review this."
- **Verify** each finding against the code, then **run** the affected interaction, because some bugs, like 3.4's, are only visible in the running app.

Close by collecting the room's findings into one list (1–5 plus the thank-you bug). That list is the starting spec for episode 5, where students implement duplicate-ID checking properly.
