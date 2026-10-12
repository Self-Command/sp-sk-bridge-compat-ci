---
description: "Task list for title-to-task implementation"
---

# Tasks: Title-to-task

**Input**: Design documents from `/specs/001-title-to-task/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/title-task.md, quickstart.md.
**Tests**: Required observed TDD using Python 3.13 standard-library unittest.
**Organization**: Exactly three cohesive tasks grouped by user story.

## Format: `[ID] [P?] [Story] Description`

Checkboxes record implementation completion; story labels map to spec.md. No [P] markers: all tasks share files and have ordered dependencies.

## Path Conventions

Source: `resume_app.py`; tests: `test_resume_app.py`; canonical task/evidence file: `specs/001-title-to-task/tasks.md`.

## Phase 1: Setup (Shared Infrastructure)

No separate setup, packaging, or directory scaffolding task is needed.

## Phase 2: Foundational (Blocking Prerequisites)

No separate foundational task is needed; normalization belongs to US1.

## Phase 3: User Story 1 - Normalize a title (Priority: P1) MVP

**Goal**: Return a trimmed, non-empty title (FR-001, FR-005).
**Independent Test**: Ordinary/already trimmed strings, ASCII/Unicode boundary whitespace, empty/whitespace-only strings, accented text, emoji, preserved interior whitespace/case and no Unicode normalization.

- [ ] T001 [US1] Write normalization tests first in `test_resume_app.py`, run `python -m unittest -v test_resume_app.NormalizeTitleTests` and observe failure before implementing `normalize_title` in `resume_app.py`; use str.strip(), preserve remaining text, and raise ValueError when empty. Data-model constraint: "str.strip() result must be non-empty; otherwise ValueError". Run the same tests and `python -m unittest discover -v` to observe green. Explicitly append actual red/green commands, exit statuses and output plus accumulated-suite results under `## T001 execution evidence` in canonical `specs/001-title-to-task/tasks.md`; never replace earlier evidence. Mark this canonical checkbox complete only after green, then commit source, tests, checkbox and evidence together in a separate T001 commit.

**Checkpoint**: US1 passes independently before T002 begins.

## Phase 4: User Story 2 - Create a task (Priority: P2)

**Goal**: Return exactly the normalized title and boolean False (FR-002, FR-005).
**Independent Test**: Complete dictionary equality, exact key set, boolean type and False value, Unicode preservation, and ValueError for empty/ASCII/Unicode whitespace-only titles.

- [ ] T002 [US2] Depends on completed and committed T001. Write task-creation tests first in `test_resume_app.py`, run `python -m unittest -v test_resume_app.MakeTaskTests` and observe failure before implementing `make_task` in `resume_app.py` using `normalize_title`; propagate ValueError. Data-model constraints: "Exactly these two keys; derived from normalized title" and "title: normalized string; completed: boolean False". Run the same tests and `python -m unittest discover -v` to observe green. Explicitly append actual red/green commands, exit statuses and output plus accumulated-suite results under `## T002 execution evidence` in canonical `specs/001-title-to-task/tasks.md`; never replace earlier evidence. Mark this canonical checkbox complete only after green, then commit source, tests, checkbox and evidence together in a separate T002 commit.

**Checkpoint**: US1 and US2 pass before T003 begins.

## Phase 5: User Story 3 - Command-line task creation (Priority: P3)

**Goal**: Print one task JSON object plus newline; apply documented exit rules (FR-003, FR-004, FR-005).
**Independent Test**: Subprocess tests using the active Python executable compare decoded JSON to the library for ordinary and Unicode titles, assert trailing newline and exit 0, and cover missing, empty, ASCII/Unicode whitespace-only and extra arguments with exit 2 and no task JSON. Key order, Unicode escaping and stderr wording remain unspecified.

- [ ] T003 [US3] Depends on completed and committed T001 and T002. Write CLI subprocess tests first in `test_resume_app.py`, run `python -m unittest -v test_resume_app.CliTests` and observe failure before implementing the single-title CLI in `resume_app.py` with standard-library argparse/json and `make_task`. Run the same tests and `python -m unittest discover -v` to observe green for all contract scenarios. Explicitly append actual red/green commands, exit statuses and output plus accumulated-suite results under `## T003 execution evidence` in canonical `specs/001-title-to-task/tasks.md`; never replace earlier evidence. Mark this canonical checkbox complete only after green, then commit source, tests, checkbox and evidence together in a separate T003 commit.

**Checkpoint**: All three stories and seven contract acceptance criteria pass.

## Phase 6: Polish & Cross-Cutting Concerns

No separate polish task. FR-006 scope exclusions and standard-library constraints apply throughout.

## Dependencies & Execution Order

T001 (US1) → T002 (US2) → T003 (US3); T003 also directly depends on T001.
Within each task: tests first → observed red → implementation → same tests green → accumulated suite green → append evidence and complete canonical checkbox → separate commit.
Non-string library inputs remain outside contract. No UI, database, network, installation, persistence, extra features or runtime dependencies.

## Parallel Examples

US1, US2 and US3 each have one cohesive task; none permits parallel implementation because both source and tests are shared and dependencies are sequential.

## Implementation Strategy

MVP: complete and independently validate US1. Incrementally add US2 then US3, preserving prior passing tests. Execute only through the bridge after the mandatory handoff succeeds; use gpt-6.1-sol, no reviewer spawns, and keep branch (finish option 3). This invocation stops before code.

## Notes

Execution evidence is append-only in this canonical file under the exact task headings specified above. Do not invent observations or mark tasks complete during generation. Preserve native task format and the three-task scope.
