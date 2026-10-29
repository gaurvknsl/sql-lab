# SQL / LAB: direction and verification

## Brief and scope

A private, local practice tool for a beginner preparing for the next day's DBMS lab. The primary job is to read a concrete question, type Oracle-style SQL/PLSQL, run it, understand a mistake, and advance. The scope is the supplied topic photo: simple/complex SQL, nested and correlated queries, procedures with parameters, functions, triggers and cursors. Assignment material supplies familiar question patterns within that boundary.

Inventory: a SQL> prompt; PL/SQL slash terminators; flight/airport/seat relationships; customer/order/item relationships; the learner's library assignments; actual source-paper mistakes; parameters and cursor rows; a 20+20 mark practice structure; fresh datasets; a beginner who needs explanations; saved drafts; and a one-night preparation window.

The screen's question: **What query should I write next, and does my attempt work?**

The signature: the student's SQL> worksheet is the main canvas, paired with the exact question and its live schema. The interface changes from SQL> to PLS> with the exercise type. The live element is real result/behavior checking across three datasets, not decorative terminal output.

## Direction

Applied skills: design-taste-frontend (app-screen workflow), design-director, and Sites (local-only path; no registration or deployment).

The app draw offered True-black flat and Data terminal. Chosen: **True-black flat, seed 118977250**. The long-session practice tool benefits from separation by lightness, restrained status color, an inverted primary action, and no ornamental navigation. No redraws.

Palette and type were explicitly kept from the user's brief: graphite grounds #141414/#1b1b1b/#242424, near-white text, neutral controls. Segoe UI is the interface face; Consolas has the single job of showing actual code and database identifiers. No downloaded fonts or external assets. The brand prompt mark is a small original SVG.

The dealt shell is a top bar with a centered workspace and no sidebar. The builder is composed as a question/reference pane and a larger worksheet pane. Color appears only on success, errors, and explanatory notices. Motion is immediate control feedback with a reduced-motion fallback; no page entrances.

## Research limits

Live reference research attempted Godly's Linear entry and Awwwards' minimal gallery, both inaccessible through the web tool. The Linear homepage at https://linear.app was readable as text, but its visual composition and interactions were not inspected. No claim is made that this is a visual recreation or that inaccessible interactions were reviewed. The concrete SQL*Plus-like interface in the user's brief remains the primary reference.

## Critique, round 1

Seen in one second: a quiet SQL question on the left and a terminal worksheet on the right.

Idea: the actual query-and-result ritual becomes the product's visual structure.

Live thing: type an answer and check real results/program behavior.

Layout words: shell=plain top bar / brief=question plus schema / work=terminal plus coach and output / chooser=selectable curriculum / review=attempt queue.

Scores (self-assessment, not an external jury): design 8.0, usability 7.8, creativity 7.5, content 9.0; weighted overall 7.9.

Top problems:

1. Desktop and phone screenshots used too much 11-12px working text. Increased schema fields, tabs, hints, and text controls to 13px; explanatory body to 14px.
2. On tablet, CSS auto-placement moved question navigation before the concept/schema row. Gave the brief's rows explicit positions.
3. On phone, the worksheet required a long scroll through references. Added a visible Write your answer action that focuses and scrolls directly to the editor, and capped reference-pane height.

## Final critique

Seen in one second: a DBMS question and an editable SQL worksheet with an obvious run action.

Idea and live thing: unchanged; the work itself is the identity.

Scores (self-assessment): design 8.4, usability 8.7, creativity 7.8, content 9.2; weighted overall 8.5.

The question carries the largest meaningful text, and the worksheet carries the largest area. Pane edges and top-bar edges align. Counts and progress are computed from actual question state; zeros are real zeros. Status does not rely on color alone. The mobile navigation is a compact top bar; the editor is one tap away. Monospace stays within code and database identifiers. No photographs, illustrations, charts, ornamental media, or invented performance figures are used; those would obstruct this task.

Remaining limits: dense schemas and long programs use contained scrolling on small screens. The editor is a deliberately simple terminal-like textarea, not a full IDE. The interpreter is a bounded educational subset, explicitly described in the application and README; it is not an Oracle installation.

## Verification

- Final design inspector: **0 FAIL, 0 WARN** at 1440, 768, and 390 pixels.
- Opened all six final fold/page screenshot files and reviewed desktop, tablet, and phone layouts.
- Source design lint: 0 FAIL; its two warnings are defensible: clock zero-padding and monospace for real code/identifiers.
- JavaScript syntax check and Python compilation passed.
- **31 automated tests passed**, including every one of the 80 reference answers on three datasets, equivalent joins/aliases, boundary values, date formatting, wrong NULL conditions, duplicates, fixture isolation, hardcoded answers, OUT mode errors, trigger effects, infinite-loop limits, and explicitly unsupported Oracle constructs.
- Actual browser checks: wrong query; retry and answer explanation; correct query; next-question progression; help off; independent solve; procedure compilation/execution with changed parameter names; round selection; reload persistence; mock start/timer/reload/finish/score/reopen/retake; and guided-to-independent review retake. The isolated test instance was stopped after checking.
- Browser error log: no application console errors during the verified flows.

All test progress was confined to a different local port, preserving the user's practice state. The earlier Oracle SQL*Plus executable could not launch in this environment, so no claim of real Oracle execution is made.

## Portable repository handoff

The repository version uses ordinary Python 3.10+ launchers on Windows, macOS and Linux, with no device-specific paths. The expanded suite contains 40 passing tests, including a real temporary HTTP server and database-connection cleanup checks on standard Python 3.13. The source PDFs, generated captures, browser progress, credentials and interpreter caches are not required to run the app and are excluded from Git. Cross-platform GitHub Actions checks are included.
