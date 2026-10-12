# Title-to-task PRD

## Intent and user story

Provide a tiny Python 3.13 standard-library compatibility fixture that turns a title into task JSON. A user automating task creation can call the library or CLI and receive the same predictable task shape. Success means every documented library and CLI behavior works.

## Approved behavior and boundaries

- `resume_app.py` exposes `normalize_title(title)` and `make_task(title)`.
- `normalize_title` accepts strings, strips surrounding whitespace, preserves the remaining text, and raises `ValueError` when the result is empty.
- `make_task` returns exactly `{"title": normalized_title, "completed": false}` (Python `False` in the library), using the same normalization and validation.
- `python resume_app.py TITLE` accepts a single title argument, prints the task as JSON, and exits 0.
- Missing, empty, or whitespace-only `TITLE` exits 2.
- No UI, database, network, installation, persistence, additional features, or runtime dependencies. Non-string library arguments are outside the contract.

## Error and Unicode cases

An empty string and a string containing only whitespace are invalid, including whitespace removed by Python's `str.strip()`. Non-empty Unicode titles are accepted. Surrounding whitespace is removed; interior whitespace, case, accents, emoji, and other remaining characters are preserved without Unicode normalization.

Builder calls: use Python's standard whitespace stripping semantics; emit one JSON object followed by a newline on stdout. Invalid CLI input produces no task JSON and may explain the error on stderr; exact diagnostic wording is unspecified. Extra positional arguments exit 2. JSON key order and Unicode escaping are unspecified, provided decoding yields the required object.

## Acceptance criteria

1. Normalizing `"  Buy milk  "` yields `"Buy milk"`; already normalized text remains unchanged.
2. Normalizing `""`, `" \t\n "`, or Unicode whitespace alone raises `ValueError`; `make_task` propagates that validation failure.
3. Unicode titles such as `"  Café ☕  "` normalize to `"Café ☕"`; interior whitespace remains intact.
4. `make_task("  Buy milk  ")` returns a dictionary with exactly the keys `title` and `completed`, the normalized title, and boolean `False`.
5. Invoking the CLI with a quoted valid title exits 0 and writes JSON that decodes to the same task dictionary.
6. Missing, empty, whitespace-only, or extra CLI arguments exit 2 and produce no task JSON on stdout.
7. The fixture uses Python 3.13 and only the standard library. Future implementation uses standard-library `unittest` and observed red/green TDD.

## Handoff boundary

This document records the approved tiny scope. Spec Kit owns the formal spec, plan, and canonical tasks next: T001 normalization and tests; T002 task creation and tests, depending on T001; T003 CLI and tests, depending on T001/T002. Each future implementation task requires a commit with its canonical checkbox and actual execution evidence. This handoff stops after the PRD and builder check; no application code, scaffolding, tests, or Superpowers writing plan is produced here.

Builder check: one fresh `gpt-6.1-sol` reviewer at low reasoning used the native brainstorming builder-check prompt and returned “nothing important left.” No material findings required changes.
