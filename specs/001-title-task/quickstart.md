# Quickstart Validation Guide

Prerequisite: Python 3.13, standard library only. No install or network access.
These commands are for the subsequent implementation phase; code and tests do
not exist yet. Run from the repository root.

## Observed TDD

For each future dependent task, write its unittest first and run
`python -m unittest discover -s tests -v`. Record the actual failure attributable
to the missing behavior before writing implementation; then record passing output.
After each task, commit source, tests, canonical tasks.md checkbox, and execution
evidence together. T002 follows T001; T003 follows both. Keep the branch.

## End-to-end Validation

```bash
python -m unittest discover -s tests -v
python resume_app.py '  Buy milk  '
python resume_app.py 'Buy  milk'
python resume_app.py '  café 🚀  '
python resume_app.py ''
python resume_app.py '   '
python resume_app.py
```

The test suite must verify both library interfaces, empty and whitespace-only
ValueError, internal spaces, ASCII and Unicode surrounding whitespace, and
Unicode content. CLI subprocess tests must parse JSON and assert exact fields,
boolean false, expected normalized title, and exit 0 for valid input. Blank,
Unicode-whitespace-only, and missing titles must exit 2 without successful task JSON.
Check each process return code independently. See [contracts](contracts/interfaces.md)
and [data model](data-model.md) for exact expected values.
