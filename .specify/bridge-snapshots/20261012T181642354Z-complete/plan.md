# Implementation Plan: Title-to-task

**Branch**: `feature/title-task-full` | **Date**: 2026-10-12 | **Spec**: [spec.md](spec.md)

**Input**: [Feature specification](spec.md), [PRD](../../docs/product/title-task-prd.md),
and [constitution](../../.specify/memory/constitution.md).

## Summary
Deliver the approved two-function library and single-title CLI in resume_app.py.
Use str.strip(), a two-key dictionary, and standard-library JSON and argument parsing.
Design ends here; canonical task generation and implementation are deferred.

## Technical Context

**Language/Version**: Python 3.13.
**Primary Dependencies**: Standard library only: json, argparse; unittest and subprocess for testing.
**Storage**: None.
**Testing**: Standard-library unittest; direct library checks and CLI subprocess checks.
**Target Platform**: Python 3.13 command-line environment, validated in this Linux checkout.
**Project Type**: Library and CLI in one module.
**Performance Goals**: No latency or throughput target approved; correctness is the acceptance gate.
**Constraints**: Preserve Unicode, empty validation, exact task object, and exit codes; no external dependencies.
**Scale/Scope**: One string input per call, no persistence or concurrency service.

## Constitution Check

| Gate | Before research | After design |
| --- | --- | --- |
| PRD contract preserved | PASS | PASS: contracts cover all seven acceptance criteria |
| Python 3.13, standard library and unittest | PASS | PASS: no third-party tools |
| Observed red/green TDD | PASS: required for future execution | PASS: validation guide requires actual evidence |
| Exactly three dependent tasks, per-task commits | PASS | PASS: future T001 → T002 → T003; T003 also depends on T001 |
| Canonical SK ownership and mandatory hooks | PASS | PASS: both guard invocations allowed; no tasks generated |
| Keep branch, zero reviewers | PASS | PASS: no integration or agent spawning |

## Project Structure

### Documentation (this feature)

```text
specs/001-title-to-task/
  spec.md
  plan.md
  research.md
  data-model.md
  quickstart.md
  contracts/title-task.md
  checklists/requirements.md
```

Future tasks.md is produced only by Spec Kit tasks, outside this invocation.

### Source Code (repository root)

Planned files, not created by this design:

```text
resume_app.py
test_resume_app.py
```

**Structure Decision**: One root module and one discoverable unittest module keep the fixture tiny.
Future task generation MUST define exactly T001 normalization/tests; T002 task creation/tests
(depending on T001); T003 CLI/tests (depending on T001/T002). Each future task commit MUST include
its canonical checkbox and actual red/green execution evidence. Keep branch, finish option 3.

## Complexity Tracking

No constitution violations or exceptions.
