# Implementation Plan: Title-to-task

**Branch**: `feature/title-task-full` | **Date**: 2026-10-12 | **Spec**: [spec.md](spec.md)

**Input**: [Specification](spec.md), [PRD](../../docs/product/title-task-prd.md),
and [constitution](../../.specify/memory/constitution.md).

## Summary

Provide the approved normalization and exact incomplete-task dictionary through
one library module and CLI. Reuse normalization in task creation and task creation
in the CLI; encode with standard-library JSON. Blank titles fail consistently.

## Technical Context

**Language/Version**: Python 3.13.
**Primary Dependencies**: Standard library only: json, argparse, unittest, subprocess.
**Storage**: None.
**Testing**: unittest; direct library assertions and CLI subprocess assertions.
**Target Platform**: Python 3.13 command-line environment; current CI uses Linux.
**Project Type**: Library/CLI.
**Performance Goals**: No numeric latency or throughput requirement; one title per invocation.
**Constraints**: Preserve str.strip Unicode behavior, internal content, exact fields,
ValueError for library blanks, and CLI exit codes 0/2; no scope expansion.
**Scale/Scope**: Two library functions and one command-line entry point, no external integrations.

## Constitution Check

| Gate | Before research | After design |
| --- | --- | --- |
| Approved PRD interfaces, Unicode, blanks, JSON and exits | Pass | Pass: contracts preserve all |
| Python 3.13, standard library and unittest | Pass | Pass: no added dependencies |
| Observed failing then passing tests | Pass: required | Pass: quickstart requires evidence |
| Exactly three dependent tasks, per-task commits | Pass | Pass: reserved for subsequent SK task generation |
| Canonical SK ownership and mandatory guards | Pass | Pass: guard allowed clarify and plan |
| Keep branch, no implementation at this stage | Pass | Pass: documentation only |

## Project Structure

### Documentation (this feature)

```text
specs/001-title-task/
  spec.md
  checklists/requirements.md
  plan.md
  research.md
  data-model.md
  contracts/interfaces.md
  quickstart.md
```

### Source Code (repository root)

Planned only; no source or test scaffolding is created in this phase:

```text
resume_app.py
tests/test_resume_app.py
```

**Structure Decision**: One module holds the library and CLI. One unittest module
covers normalization, task creation, and CLI behavior. Future SK tasks MUST be
T001 normalization/tests, T002 task creation/tests depending on T001, T003 CLI/tests
depending on T001/T002, each committed with checkbox and observed execution evidence.
No tasks.md is generated now.

## Complexity Tracking

No constitution violations or additional abstractions are required.
