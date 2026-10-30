# SQL / LAB

A local, exam-focused Oracle SQL and PL/SQL practice website. **107 exercises, 12 selectable rounds, and a 60-minute 40-mark mock.**

[![Tests](https://github.com/gaurvknsl/sql-lab/actions/workflows/tests.yml/badge.svg)](https://github.com/gaurvknsl/sql-lab/actions/workflows/tests.yml)

## Run on another laptop

You need:

- **Python 3.10 or newer**, with its standard-library SQLite support. The normal installers from [python.org](https://www.python.org/downloads/) include it. On Windows, enable the Python launcher or add Python to PATH during installation.
- **Git**, to clone and pull updates. Get it from [git-scm.com](https://git-scm.com/downloads), or download and extract this repository's ZIP instead.
- A modern web browser.

No Oracle installation, Codex runtime, Node.js, API key, account, pip packages, virtual environment, database setup, or frontend build is needed. All source, exercise data, styles, and icons are included. After the first clone, practice works offline.

### Windows

Open PowerShell or Command Prompt:

```powershell
git clone https://github.com/gaurvknsl/sql-lab.git
cd sql-lab
py -3 start.py
```

You can also double-click **Start Lab.cmd** in the cloned folder. If your installation uses `python` instead of `py`, run `python start.py`.

### macOS or Linux

```sh
git clone https://github.com/gaurvknsl/sql-lab.git
cd sql-lab
python3 start.py
```

Alternatively, run `./start.sh` or `sh start.sh`.

The browser opens at **http://127.0.0.1:8765**. Keep the server's terminal open while practising. If the browser does not open automatically, enter that address yourself. Stop the server with **Ctrl+C** in the terminal. Starting the launcher twice reopens the existing local app.

If another application occupies that port, run `py -3 start.py --port 8766` on Windows or `python3 start.py --port 8766` on macOS/Linux. Open the printed URL.

### Get updates later

Stop the server, open a terminal in the cloned folder, then run:

```sh
git pull --ff-only
```

Start the app again using the same command as above. There are no dependencies to reinstall. Browser-saved progress stays on that laptop when you use the same browser profile and port; it is not stored in Git or transferred to another laptop.

For a server without automatic browser opening, use `python server.py` (or `py -3 server.py` / `python3 server.py`). Open the website through the server: opening `public/index.html` directly cannot reach the exercise runner.

## How to practise

### Today's exam: hospital assignment 5/6

Choose **Today's exam · Hospital** at the top of the round picker, or open **http://127.0.0.1:8765/?round=hospital**. It contains 27 questions: the four assignment queries, 16 additional SQL questions on the same schema, and seven PL/SQL exercises covering SELECT INTO, cursors, procedures, functions and triggers.

The visible PATIENT, DOCTOR, WARD and PHARMACY rows reproduce the inserted sample values in the assignment screenshots, including ward **90**, the trailing space in **ORTHO **, and the September 2026 purchases. No patient records beyond that assignment's synthetic examples are inferred. Separate grading datasets add explicit edge cases.

The original prompt names ward 5, while the inserted rows and submitted query use ward 90; the practice question follows the actual rows and explains this. The original April query correctly has no visible matches, and uses a month function rather than applying LIKE to a DATE. “Joint pains” follows the assignment's stated orthopedic-doctor interpretation because there is no diagnosis field. The pharmacy key is `(billno, medicinename)` and the ward key is `(wno, bed_no)`.

Choose any round from the selector at the top. Start with First queries if needed. Read the question and use Schema or Sample data to understand the tables. Type the query and select Run query, or press Ctrl+Enter. On an incorrect attempt, use Try again or View answer. A correct attempt offers the next question. You can skip and return to any question from Question list.

Help mode shows the relevant concept, progressive hints, and common-error diagnostics while typing. Normal mode hides these. Reference contains only the SQL and PL/SQL patterns used in the rounds. Viewing an answer does not complete a question. Completed questions that used help are distinguished from independent solves and remain in Review.

Drafts and progress are saved in this browser's local storage. Keep the same browser and port to retain them. Clearing browser data or switching browser profiles removes that local history. Review offers a JSON export and a confirmed reset of local progress.

The mock is five SQL questions at 4 marks each and two PL/SQL questions at 10 marks each. It is a practice structure based on the topic photo, not a prediction of the actual paper. Its 60-minute timer keeps running across navigation and reloads. Independent and assisted marks are reported separately; the real examiner may award partial credit.

## Syllabus boundary

Included: simple and complex SELECT queries, Oracle string/NULL/date functions used by the questions, joins, grouping, nested/correlated queries, PL/SQL foundations needed for procedures with parameters, functions, triggers, and cursors.

The library round adapts relevant question patterns from DBMS assignments and a lab assessment. Sample records are invented for practice; they are not copied personal records. The source PDFs are not required or included. Object types, VARRAYs, schema-design/DDL exercises, views, unrelated puzzles, and other additional assignment topics are not lessons or scored tasks here.

The sample-paper round covers all ten SQL questions, both cascade-trigger patterns, and both cursor questions. Corrections are attached to the relevant questions:

- The single-arrival FLNO schema cannot model one flight number arriving in multiple Kerala cities. The corrected coverage task asks for airlines reaching every represented Kerala city.
- “All ... if any” explicitly preserves unmatched flights/customers using LEFT JOIN.
- “Delete foreign keys” means delete dependent rows, not drop a constraint.
- ORDER becomes ORDERS, date fields have explicit names, and the customer's address is flattened.
- The introductory update-cascade exercise targets FLIGHT -> SEAT; the sample-paper task also requires AIRPORT -> both FLIGHT references. The sample delete task covers both CUSTOMER -> ORDERS and ITEM -> ORDERS. Key updates are single-key changes to unused keys. Real Oracle requires compatible foreign-key constraint timing, such as deferrable constraints deferred before the key change; the sandbox does not enforce Oracle constraint timing.

## What the runner is, and its limits

This is a **local teaching sandbox, not a full Oracle database**. It does not connect to, reset, or modify the Oracle installation on this laptop.

SQL runs against fresh SQLite in-memory databases, with common Oracle date literals, SYSDATE, NVL/NVL2, TO_DATE, TO_CHAR, TRUNC, MOD, DECODE, INITCAP and concatenation patterns adapted. Result comparison retains duplicate counts, permits arbitrary aliases, and checks order when the task requests it. Three datasets vary prices, ties, counts, names, missing matches, and dates so hardcoded display-only answers fail.

PL/SQL is tokenized, parsed and interpreted; it is not graded by matching its text to the reference. The runner supports the subset used by these exercises: variables, records, SELECT INTO, IF/ELSIF/ELSE, loops, explicit and parameterized cursors, manual OPEN/FETCH/CLOSE, ordinary exceptions, procedures and parameter modes, functions, and row-trigger actions. Routines are invoked with multiple inputs, and trigger effects are checked on whole-table snapshots. Equivalent supported programs can pass.

It does not provide complete Oracle parsing, type enforcement, NLS behavior, implicit conversions, NULL concatenation in arbitrary SQL, transactions/constraint timing, all date format models, SQL*Plus commands, packages, advanced trigger features, dynamic SQL, or every legal PL/SQL construct. Unimplemented constructs should produce an explicit error, and not be mistaken for a verdict from Oracle. Supported examples are Oracle-style learning material; use the actual lab Oracle environment for final compatibility checks when available.

Execution has input, row, instruction and loop limits. The HTTP server listens only on 127.0.0.1, rejects cross-origin POSTs, and requires no credentials. All exercise databases live in memory and are discarded after checking. The lab clock is fixed at **29 October 2026** so relative-date answers remain reproducible.

## Development

- `start.py`, `Start Lab.cmd`, `start.sh`: portable launchers.
- `server.py`: local HTTP endpoints and behavioral grading.
- `engine.py`: SQLite fixtures, Oracle helpers, PL/SQL parser and bounded interpreter.
- `questions.py`: curriculum, hints, schemas, sample-paper corrections and reference solutions.
- `hospital.py`: assignment 5/6 hospital rows, hidden variants, schema and the dedicated exam round.
- `public/`: buildless HTML, CSS and JavaScript frontend.
- `test_lab.py`: reference, alternate-answer, negative and runtime tests.
- `test_http.py`: real HTTP endpoint and asset tests.
- `test_hospital.py`: original-row fidelity and hospital-query edge cases.
- `.github/workflows/tests.yml`: Windows/Linux checks on Python 3.10 and 3.13, plus macOS on Python 3.13.
- `DESIGN.md`: brief, direction and visual QA notes.

Run the checks with:

```powershell
python -m unittest discover -v
```

Use `py -3` on Windows or `python3` on macOS/Linux if that is the Python command installed on your machine. Tests use only the Python standard library and temporary loopback ports. No credentials or internet access are required for the test suite.
