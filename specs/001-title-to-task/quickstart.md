# Validation Quickstart

Design only: these commands become runnable after the future implementation.
Prerequisite: Python 3.13, repository root as working directory; no installation required.
See [public contract](contracts/title-task.md) and [data model](data-model.md).

```bash
python --version
python -m unittest discover -v
python resume_app.py "  Buy milk  "
python resume_app.py "  Café ☕  "
python resume_app.py ""
python resume_app.py "   "
python resume_app.py
python resume_app.py one two
```

The first two title commands exit 0 and emit one JSON object plus newline, decoding to
`{"title": "Buy milk", "completed": false}` and `{"title": "Café ☕", "completed": false}`.
The last four commands each exit 2 and emit no task JSON; stderr wording is not asserted.

Future unittest coverage MUST exercise ordinary/already normalized text, empty input,
ASCII and Unicode whitespace, emoji/accented text, preserved interior whitespace,
propagated ValueError, exact key set and boolean False. CLI subprocess tests MUST check
return codes, decoded output equality, trailing newline, and all invalid argument categories.

For each future canonical task, write its tests, run and retain the actual failing output,
implement only the task, then run the same tests and the accumulated suite to observe green.
Record commands/results with the completed canonical checkbox in that task's separate commit.
Do not claim observed TDD from this design-only invocation. Keep the feature branch.
