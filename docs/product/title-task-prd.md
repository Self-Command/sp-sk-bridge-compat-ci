# Title-to-task PRD

## Intent and user story

Provide a fixed, tiny compatibility fixture for an automation user who needs
to create task JSON from a title. As that user, I can call a Python library or
run a CLI with a title and receive the same normalized, incomplete task.
Success means every library and CLI behavior below is satisfied.

## Boundaries and constraints

Use Python 3.13 and its standard library only, with the library and CLI in
`resume_app.py`. No UI, database, network, installation, persistence, runtime
dependencies, or additional features. Silent acceptance of blank titles,
extra task fields, or different library/CLI normalization would be failures.

This PRD records approved requirements; formal spec, plan, and tasks belong
to Spec Kit next. This stage produces no application code, scaffolding, or
tests. The eventual implementation uses standard-library `unittest` and
observed red/green TDD, with exactly three ordered cohesive tasks:
T001 normalization and tests; T002 task creation and tests, depending on
T001; T003 CLI and tests, depending on T001/T002. Each task is committed with
its canonical checkbox and actual execution evidence.

## Required behavior and acceptance criteria

| Surface | Acceptance criterion |
| --- | --- |
| `normalize_title(title)` | Strip surrounding whitespace from a string and return the result. Preserve internal whitespace and non-empty Unicode content. |
| Empty input | `normalize_title("")` and whitespace-only strings raise `ValueError`. |
| `make_task(title)` | Return exactly `{"title": normalized_title, "completed": False}` as a Python dictionary, using the same normalization and blank-title rejection. |
| CLI success | `python resume_app.py TITLE` with one non-empty title prints the task as JSON and exits 0. JSON contains exactly `title` and `completed`, with JSON boolean `false`. |
| CLI errors | An empty, whitespace-only, or missing `TITLE` exits 2. It must not emit a successful task JSON. |
| Unicode | Non-empty Unicode titles are accepted by both entry points and preserved in the decoded JSON title after trimming. |

For example, `"  Buy milk  "` becomes title `"Buy milk"`; `"Buy  milk"`
retains its internal double space; `"  café 🚀  "` becomes `"café 🚀"`.
Python string stripping defines surrounding whitespace, including Unicode
whitespace recognized by `str.strip()`.

## Builder discretion

JSON key order, formatting, and Unicode escaping are unspecified: decoded
JSON must satisfy the contract. Error-message wording and diagnostic output
stream, handling of extra CLI arguments, and inputs other than library
strings are left to the builder without extending the supported scope.
No product questions remain; these requirements come from
`APPROVED_INPUTS.md` and the user's approved fixture intent.
