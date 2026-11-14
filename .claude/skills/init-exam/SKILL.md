---
name: init-exam
description: Set up Cert PT for a new certification exam. Reads the official study guide PDF in guide/, extracts domains, weights and objectives, asks the learner only what it can't infer (exam date, day 0, known platform, schedule, practice exams), then generates CLAUDE.md, ObjectiveTracker.md, MissLog.md, QuickRef.md, LessonsLearned.md, StudyPlan.md and exam.json from templates/. Use when the user runs /init-exam or asks to set up Petey / Cert PT for an exam.
---

# /init-exam: set up Petey for an exam

You're setting up a Cert PT study kit. Work through the steps in order. Keep messages short and plain.

## 0. Greet and check

- Open with one or two lines as Petey, e.g. "Petey here, your Cert PT. Let's get your exam set up: I'll read the guide, ask a few questions, then write your plan." This greeting is the only persona moment; after it, be plain and direct.
- If any of `CLAUDE.md`, `ObjectiveTracker.md`, `MissLog.md`, `QuickRef.md`, `LessonsLearned.md`, `StudyPlan.md` or `exam.json` exist at the repo root, list them and stop unless the user explicitly says to overwrite. They may hold weeks of progress.

## 1. Find and read the guide

- Look for `guide/*.pdf`. None: ask the user to put the official study guide / skills outline PDF in `guide/` (a saved web page printed to PDF is fine). More than one: ask which.
- Read the whole PDF with the Read tool (use `pages` in chunks of up to 20 for long guides).

## 2. Extract

Pull out, and keep a note of the page each came from:
- Exam name, code, guide version or date, duration, question count, question types, passing score if stated, and anything said about unscored or beta items.
- **Domains** with weights. Keep ranges as written (e.g. `30–35%`) and use the midpoint for sizing.
- **Objectives** under each domain, with their bullets. If the guide doesn't number them (common in skills outlines), number them `1.1, 1.2…` within each domain.
- **Sample questions**: note their *style* only (scenario + constraint + options, multi-select, etc.). Never copy them into any generated file.
- Items marked not tested, preview, beta, or "not until GA".
- **Vendor → trusted docs domain(s)**, e.g. docs.snowflake.com, learn.microsoft.com, docs.aws.amazon.com, cloud.google.com/docs, docs.databricks.com. Add the vendor's official training/quickstart site if the guide names it.
- **Renamed-products draft:** product or feature names in the guide that have older names a model or a practice bank might use (or recent rebrands you know of). Every row's status is `verify` at init.

## 3. Propose the sessions

- One objective = one session. **Split into a/b** when an objective is big: roughly more than ~6 bullets, or more than ~1.5× the average bullets per objective, or in a domain worth ≥ 25% with dense bullets. Split along natural seams in the bullets; each half gets a scope line listing its bullets.
- Mark light objectives (few bullets, low weight) as candidates for double days.
- Show the result as a compact table (ID · scope · light?) with totals per domain and overall, and ask the user to confirm or adjust before continuing.

## 4. Ask only what you can't infer

Use AskUserQuestion, at most two rounds. Skip any question the user already answered.
1. **Exam date and time** (with timezone), or "not booked yet" → ask for a target date.
2. **Day 0**: today, or an earlier first study day or baseline exam date?
3. **Platform you know best**, for analogies (e.g. Microsoft Fabric, AWS, Databricks, Postgres, on-prem SQL Server); and any platforms **not** to use for analogies. One line of background (role, years).
4. **Schedule**: which days you can study, roughly how many hours a week, and whether double days (two sessions with a break between) are OK.
5. **Practice exams** you have or plan to buy: the official practice test, if the vendor sells one, and any third-party banks. These shape the mock phase and readiness gate.
6. **Confirm** the trusted docs domain(s) and the not-tested list.
7. **Hot topics:** any topics the learner has seen in pass reports or heard from colleagues (optional; they can add them later).

## 5. Build the schedule

- Window = day 0 → the day before the exam.
- Reserve, from the end: **1 light day** (review only) the day before the exam, a **buffer** of ~2 days before that, and a **mock phase** of ~25–30% of the window (min 3 days) before the buffer. The rest is content.
- Order domains by weight, highest first, unless the user asks otherwise. Keep a domain's sessions together.
- Fill study days with one session each. Use double days (light objective + normal one) only where the user allowed them and only when needed to fit. Never more than 3 sessions a day.
- If the content doesn't fit, say so plainly with the numbers, and offer options: double days, a shorter mock phase (not below 3 days), or a later exam date. Don't silently compress.
- If there's no booked date and the user wants a suggestion, size it from the session count and study days, plus the mock phase and buffer.

## 6. Write the files

Fill each template in `templates/` and write it to the repo root without the `.tmpl` suffix. Replace every `{{placeholder}}`; none may remain. Exact formats matter: `petey/build_dashboard.py` parses them.

- **`ObjectiveTracker.md`**
  - `{{schedule_rows}}`: one row per study day, **date first in ISO format with the weekday**: `| 2026-10-08 Thu | 1.1 + 1.2 | Double: 1.2 is light |`. Then one row per non-content phase: `| 2026-10-26 Mon → | Mock phase | See StudyPlan.md |`.
  - `{{domain_sections}}`: for each domain, this layout. **The heading format is exact:**

    ```
    ## Domain 1: Domain name (31%)

    | # | Session scope (from guide) | Planned | Prior misses | Status | Quiz (/7) | 🔥 | Hands-on | Date |
    |---|---|---|---|---|---|---|---|---|
    | 1.1 | short scope listing the bullets | 2026-10-08 | 0 | ⬜ | | | | |
    ```

    Weight ranges go in as written: `(30–35%)`.
  - `{{checkpoint_rows}}`: one row per domain: `| End of Domain N | YYYY-MM-DD | | | | | |`.
  - `{{mock_rows}}`: one row per planned mock from the practice exams the user has, in date order: `| Mock 1 | YYYY-MM-DD | | | | | after Domain 2 |`. The official practice test, if any, goes last in the mock phase. None planned: `| (none planned) | | | | | | |`.
- **`MissLog.md`**: header + template entry only. No entries.
- **`CLAUDE.md`**: `{{renamed_rows}}` as table rows with status `verify`; `{{exam_datetime_text}}` like `Sat 7 Nov 2026, 08:00 ACDT`; `{{not_tested_list}}` = "none listed" if empty.
- **`StudyPlan.md`**: `{{phase_rows}}` one row per domain block plus mocks, buffer, light day and exam. `{{domain_check}}`, `{{mock_plan}}` and `{{readiness_gate}}` come from the practice exams the user has. The readiness gate is: the official practice test result if one exists (the only calibrated signal) + every tracker row ✅ + bank scores as a secondary signal only. `{{resources}}`: the guide, the docs domain(s), and the user's practice exams (names only). `{{hot_topic_rows}}`: one row per hot topic the user gave, `| Topic | source | N.M bullet it fits | ⬜ |` (map each to the closest guide bullet; if none fits, say so in that cell). None given: a single row `| (none yet) | | | |`.
- **`QuickRef.md`, `LessonsLearned.md`**: fill the header placeholders.
- **`exam.json`**: ISO dates; `exam_time` as `HH:MM` (or `""`). Drop a phase entry if it has zero days. Must be valid JSON.

Don't copy guide text beyond objective names and short scope lines, and never copy sample questions.

## 7. Check and hand over

- Run `python petey/build_dashboard.py`. It must report all objectives, 0 MissLog entries and 0 unmapped. If it errors, fix the generated files (not the script) and re-run.
- Run `python petey/build_game.py` (the gamified view). It should report 0 XP and no errors.
- Finish with a short "what next" (≤5 lines), e.g.:
  - Files written; your private progress is gitignored.
  - Open `Dashboard.html` to see the plan.
  - Start a session any time with "next objective". Say "pause" to stop mid-session.
  - First session: `<id> <scope>` on `<date>`.
