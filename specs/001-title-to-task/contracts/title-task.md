# Public Contract: Title-to-task

Authoritative source: [PRD](../../../docs/product/title-task-prd.md), including all seven acceptance criteria.

## Library: resume_app.py

- normalize_title(title): string → string. Return title.strip(); raise ValueError if empty.
- make_task(title): string → dictionary. Return exactly
  `{"title": normalize_title(title), "completed": False}`; propagate ValueError.
- Non-string inputs are outside contract. Remaining Unicode text and interior whitespace
  are preserved; no case conversion or Unicode normalization.

## CLI: python resume_app.py TITLE

| Invocation | stdout | Exit |
| --- | --- | --- |
| Exactly one valid title | One JSON object plus newline; decodes to library task | 0 |
| Missing TITLE | No task JSON | 2 |
| Empty TITLE | No task JSON | 2 |
| Whitespace-only TITLE, including Unicode whitespace | No task JSON | 2 |
| Extra positional arguments | No task JSON | 2 |

A valid example is `{"title": "Buy milk", "completed": false}`. Key order and Unicode
escaping are unspecified. Diagnostics may appear on stderr with unspecified wording.

## Acceptance Matrix

1. Ordinary surrounding whitespace and already trimmed strings: exact normalized title.
2. Empty, ASCII whitespace-only, Unicode whitespace-only: ValueError from both library functions.
3. Café ☕ and interior whitespace: exact preservation after stripping.
4. Task dictionary: exact key set; completed has boolean type and is False.
5. Valid CLI: decoded dictionary equality, one JSON object, trailing newline, exit 0.
6. Missing/empty/whitespace/extra CLI arguments: exit 2, no task JSON.
7. Python 3.13; standard library only; unittest with observed red/green evidence in future execution.
