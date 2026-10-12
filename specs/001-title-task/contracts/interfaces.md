# Public Interface Contracts

Authority: [PRD](../../../docs/product/title-task-prd.md).

## Library: resume_app.py

- normalize_title(title: str) returns title.strip(); if the result is empty,
  raises ValueError. Internal whitespace and non-empty Unicode content remain unchanged.
- make_task(title: str) applies that normalization and returns exactly
  `{"title": normalized_title, "completed": False}`. Blank titles raise ValueError.
- Non-string inputs are outside the supported contract.

## CLI

Invocation: `python resume_app.py TITLE` (one quoted argument when containing spaces).

| Input | stdout contract | Exit |
| --- | --- | --- |
| Valid title | JSON object with exactly title and completed=false | 0 |
| Empty or whitespace-only title | No successful task JSON | 2 |
| Missing TITLE | No successful task JSON | 2 |

Decoded Unicode title equals the stripped input. Key order, JSON formatting and
Unicode escaping are not contractual. Error wording and diagnostic stream are
not contractual. Planned builder choices: argparse diagnostics on stderr, reject
extra arguments, and default json.dumps formatting/escaping.

Examples: `"  Buy milk  "` → `{"title": "Buy milk", "completed": false}`;
`"Buy  milk"` retains both internal spaces; `"  café 🚀  "` decodes to `"café 🚀"`.
