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

- [x] T001 [US1] Write normalization tests first in `test_resume_app.py`, run `python -m unittest -v test_resume_app.NormalizeTitleTests` and observe failure before implementing `normalize_title` in `resume_app.py`; use str.strip(), preserve remaining text, and raise ValueError when empty. Data-model constraint: "str.strip() result must be non-empty; otherwise ValueError". Run the same tests and `python -m unittest discover -v` to observe green. Explicitly append actual red/green commands, exit statuses and output plus accumulated-suite results under `## T001 execution evidence` in canonical `specs/001-title-to-task/tasks.md`; never replace earlier evidence. Mark this canonical checkbox complete only after green, then commit source, tests, checkbox and evidence together in a separate T001 commit.

**Checkpoint**: US1 passes independently before T002 begins.

## Phase 4: User Story 2 - Create a task (Priority: P2)

**Goal**: Return exactly the normalized title and boolean False (FR-002, FR-005).
**Independent Test**: Complete dictionary equality, exact key set, boolean type and False value, Unicode preservation, and ValueError for empty/ASCII/Unicode whitespace-only titles.

- [x] T002 [US2] Depends on completed and committed T001. Write task-creation tests first in `test_resume_app.py`, run `python -m unittest -v test_resume_app.MakeTaskTests` and observe failure before implementing `make_task` in `resume_app.py` using `normalize_title`; propagate ValueError. Data-model constraints: "Exactly these two keys; derived from normalized title" and "title: normalized string; completed: boolean False". Run the same tests and `python -m unittest discover -v` to observe green. Explicitly append actual red/green commands, exit statuses and output plus accumulated-suite results under `## T002 execution evidence` in canonical `specs/001-title-to-task/tasks.md`; never replace earlier evidence. Mark this canonical checkbox complete only after green, then commit source, tests, checkbox and evidence together in a separate T002 commit.

**Checkpoint**: US1 and US2 pass before T003 begins.

## Phase 5: User Story 3 - Command-line task creation (Priority: P3)

**Goal**: Print one task JSON object plus newline; apply documented exit rules (FR-003, FR-004, FR-005).
**Independent Test**: Subprocess tests using the active Python executable compare decoded JSON to the library for ordinary and Unicode titles, assert trailing newline and exit 0, and cover missing, empty, ASCII/Unicode whitespace-only and extra arguments with exit 2 and no task JSON. Key order, Unicode escaping and stderr wording remain unspecified.

- [x] T003 [US3] Depends on completed and committed T001 and T002. Write CLI subprocess tests first in `test_resume_app.py`, run `python -m unittest -v test_resume_app.CliTests` and observe failure before implementing the single-title CLI in `resume_app.py` with standard-library argparse/json and `make_task`. Run the same tests and `python -m unittest discover -v` to observe green for all contract scenarios. Explicitly append actual red/green commands, exit statuses and output plus accumulated-suite results under `## T003 execution evidence` in canonical `specs/001-title-to-task/tasks.md`; never replace earlier evidence. Mark this canonical checkbox complete only after green, then commit source, tests, checkbox and evidence together in a separate T003 commit.

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

## T001 execution evidence

Python 3.13.16; observed missing-module assertion failures before implementation.

red: `python -m unittest -v test_resume_app.NormalizeTitleTests`; exit status 1.

```text
test_preserves_remaining_characters (test_resume_app.NormalizeTitleTests.test_preserves_remaining_characters) ... FAIL
test_rejects_empty_titles (test_resume_app.NormalizeTitleTests.test_rejects_empty_titles) ... FAIL
test_trims_boundary_whitespace (test_resume_app.NormalizeTitleTests.test_trims_boundary_whitespace) ... FAIL

======================================================================
FAIL: test_preserves_remaining_characters (test_resume_app.NormalizeTitleTests.test_preserves_remaining_characters)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/sp-sk-bridge-compat-ci/sp-sk-bridge-compat-ci/.runtime/latest-linux/projects/title-task-full/test_resume_app.py", line 7, in setUp
    self.assertIsNotNone(importlib.util.find_spec("resume_app"), "normalization module is missing")
    ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: unexpectedly None : normalization module is missing

======================================================================
FAIL: test_rejects_empty_titles (test_resume_app.NormalizeTitleTests.test_rejects_empty_titles)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/sp-sk-bridge-compat-ci/sp-sk-bridge-compat-ci/.runtime/latest-linux/projects/title-task-full/test_resume_app.py", line 7, in setUp
    self.assertIsNotNone(importlib.util.find_spec("resume_app"), "normalization module is missing")
    ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: unexpectedly None : normalization module is missing

======================================================================
FAIL: test_trims_boundary_whitespace (test_resume_app.NormalizeTitleTests.test_trims_boundary_whitespace)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/sp-sk-bridge-compat-ci/sp-sk-bridge-compat-ci/.runtime/latest-linux/projects/title-task-full/test_resume_app.py", line 7, in setUp
    self.assertIsNotNone(importlib.util.find_spec("resume_app"), "normalization module is missing")
    ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: unexpectedly None : normalization module is missing

----------------------------------------------------------------------
Ran 3 tests in 0.001s

FAILED (failures=3)
```

green: `python -m unittest -v test_resume_app.NormalizeTitleTests`; exit status 0.

```text
test_preserves_remaining_characters (test_resume_app.NormalizeTitleTests.test_preserves_remaining_characters) ... ok
test_rejects_empty_titles (test_resume_app.NormalizeTitleTests.test_rejects_empty_titles) ... ok
test_trims_boundary_whitespace (test_resume_app.NormalizeTitleTests.test_trims_boundary_whitespace) ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.001s

OK
```

suite: `python -m unittest discover -v`; exit status 0.

```text
test_preserves_remaining_characters (test_resume_app.NormalizeTitleTests.test_preserves_remaining_characters) ... ok
test_rejects_empty_titles (test_resume_app.NormalizeTitleTests.test_rejects_empty_titles) ... ok
test_trims_boundary_whitespace (test_resume_app.NormalizeTitleTests.test_trims_boundary_whitespace) ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.000s

OK
```

## Injected fault recovery (T001 remains complete)

Systematic debugging: observed nine failures in existing NormalizeTitleTests (exit 1). Git diff isolated the appended lambda rebinding; it bypassed the original strip/ValueError implementation. Removed only the rebinding, restoring committed T001 without reimplementing its task.

```text
test_preserves_remaining_characters (test_resume_app.NormalizeTitleTests.test_preserves_remaining_characters) ... 
  test_preserves_remaining_characters (test_resume_app.NormalizeTitleTests.test_preserves_remaining_characters) (title='  MiXeD  interior\tspace  ') ... FAIL
  test_preserves_remaining_characters (test_resume_app.NormalizeTitleTests.test_preserves_remaining_characters) (title='  Café ☕  ') ... FAIL
  test_preserves_remaining_characters (test_resume_app.NormalizeTitleTests.test_preserves_remaining_characters) (title='  Café  ') ... FAIL
test_rejects_empty_titles (test_resume_app.NormalizeTitleTests.test_rejects_empty_titles) ... 
  test_rejects_empty_titles (test_resume_app.NormalizeTitleTests.test_rejects_empty_titles) (title='') ... FAIL
  test_rejects_empty_titles (test_resume_app.NormalizeTitleTests.test_rejects_empty_titles) (title=' \t\n ') ... FAIL
  test_rejects_empty_titles (test_resume_app.NormalizeTitleTests.test_rejects_empty_titles) (title='\u2003\xa0') ... FAIL
test_trims_boundary_whitespace (test_resume_app.NormalizeTitleTests.test_trims_boundary_whitespace) ... 
  test_trims_boundary_whitespace (test_resume_app.NormalizeTitleTests.test_trims_boundary_whitespace) (title='  Buy milk  ') ... FAIL
  test_trims_boundary_whitespace (test_resume_app.NormalizeTitleTests.test_trims_boundary_whitespace) (title='\t\n Buy milk\r ') ... FAIL
  test_trims_boundary_whitespace (test_resume_app.NormalizeTitleTests.test_trims_boundary_whitespace) (title='\u2003Café ☕\xa0') ... FAIL

======================================================================
FAIL: test_preserves_remaining_characters (test_resume_app.NormalizeTitleTests.test_preserves_remaining_characters) (title='  MiXeD  interior\tspace  ')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/sp-sk-bridge-compat-ci/sp-sk-bridge-compat-ci/.runtime/latest-linux/projects/title-task-full/test_resume_app.py", line 23, in test_preserves_remaining_characters
    self.assertEqual(self.app.normalize_title(title), expected)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: '  MiXeD  interior\tspace  ' != 'MiXeD  interior\tspace'
-   MiXeD  interior	space  
? --               	     --
+ MiXeD  interior	space


======================================================================
FAIL: test_preserves_remaining_characters (test_resume_app.NormalizeTitleTests.test_preserves_remaining_characters) (title='  Café ☕  ')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/sp-sk-bridge-compat-ci/sp-sk-bridge-compat-ci/.runtime/latest-linux/projects/title-task-full/test_resume_app.py", line 23, in test_preserves_remaining_characters
    self.assertEqual(self.app.normalize_title(title), expected)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: '  Café ☕  ' != 'Café ☕'
-   Café ☕  
? --      --
+ Café ☕


======================================================================
FAIL: test_preserves_remaining_characters (test_resume_app.NormalizeTitleTests.test_preserves_remaining_characters) (title='  Café  ')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/sp-sk-bridge-compat-ci/sp-sk-bridge-compat-ci/.runtime/latest-linux/projects/title-task-full/test_resume_app.py", line 23, in test_preserves_remaining_characters
    self.assertEqual(self.app.normalize_title(title), expected)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: '  Café  ' != 'Café'
-   Café  
? --     --
+ Café


======================================================================
FAIL: test_rejects_empty_titles (test_resume_app.NormalizeTitleTests.test_rejects_empty_titles) (title='')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/sp-sk-bridge-compat-ci/sp-sk-bridge-compat-ci/.runtime/latest-linux/projects/title-task-full/test_resume_app.py", line 28, in test_rejects_empty_titles
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_rejects_empty_titles (test_resume_app.NormalizeTitleTests.test_rejects_empty_titles) (title=' \t\n ')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/sp-sk-bridge-compat-ci/sp-sk-bridge-compat-ci/.runtime/latest-linux/projects/title-task-full/test_resume_app.py", line 28, in test_rejects_empty_titles
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_rejects_empty_titles (test_resume_app.NormalizeTitleTests.test_rejects_empty_titles) (title='\u2003\xa0')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/sp-sk-bridge-compat-ci/sp-sk-bridge-compat-ci/.runtime/latest-linux/projects/title-task-full/test_resume_app.py", line 28, in test_rejects_empty_titles
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_trims_boundary_whitespace (test_resume_app.NormalizeTitleTests.test_trims_boundary_whitespace) (title='  Buy milk  ')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/sp-sk-bridge-compat-ci/sp-sk-bridge-compat-ci/.runtime/latest-linux/projects/title-task-full/test_resume_app.py", line 16, in test_trims_boundary_whitespace
    self.assertEqual(self.app.normalize_title(title), expected)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: '  Buy milk  ' != 'Buy milk'
-   Buy milk  
? --        --
+ Buy milk


======================================================================
FAIL: test_trims_boundary_whitespace (test_resume_app.NormalizeTitleTests.test_trims_boundary_whitespace) (title='\t\n Buy milk\r ')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/sp-sk-bridge-compat-ci/sp-sk-bridge-compat-ci/.runtime/latest-linux/projects/title-task-full/test_resume_app.py", line 16, in test_trims_boundary_whitespace
    self.assertEqual(self.app.normalize_title(title), expected)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: '\t\n Buy milk\r ' != 'Buy milk'
- 	
-  Buy milk
? -        ^
+ Buy milk
?         ^
-  


======================================================================
FAIL: test_trims_boundary_whitespace (test_resume_app.NormalizeTitleTests.test_trims_boundary_whitespace) (title='\u2003Café ☕\xa0')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/sp-sk-bridge-compat-ci/sp-sk-bridge-compat-ci/.runtime/latest-linux/projects/title-task-full/test_resume_app.py", line 16, in test_trims_boundary_whitespace
    self.assertEqual(self.app.normalize_title(title), expected)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: '\u2003Café ☕\xa0' != 'Café ☕'
-  Café ☕ 
? -      -
+ Café ☕


----------------------------------------------------------------------
Ran 3 tests in 0.003s

FAILED (failures=9)
```

Recovery green: `python -m unittest discover -v`; exit 0.
```text
test_preserves_remaining_characters (test_resume_app.NormalizeTitleTests.test_preserves_remaining_characters) ... ok
test_rejects_empty_titles (test_resume_app.NormalizeTitleTests.test_rejects_empty_titles) ... ok
test_trims_boundary_whitespace (test_resume_app.NormalizeTitleTests.test_trims_boundary_whitespace) ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.000s

OK
```

## T002 execution evidence

red: `python -m unittest -v test_resume_app.MakeTaskTests`; exit status 1.
```text
test_exact_task_shape (test_resume_app.MakeTaskTests.test_exact_task_shape) ... FAIL
test_rejects_empty_titles (test_resume_app.MakeTaskTests.test_rejects_empty_titles) ... FAIL

======================================================================
FAIL: test_exact_task_shape (test_resume_app.MakeTaskTests.test_exact_task_shape)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/sp-sk-bridge-compat-ci/sp-sk-bridge-compat-ci/.runtime/latest-linux/projects/title-task-full/test_resume_app.py", line 35, in setUp
    self.assertTrue(callable(getattr(self.app, "make_task", None)), "make_task is missing")
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: False is not true : make_task is missing

======================================================================
FAIL: test_rejects_empty_titles (test_resume_app.MakeTaskTests.test_rejects_empty_titles)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/sp-sk-bridge-compat-ci/sp-sk-bridge-compat-ci/.runtime/latest-linux/projects/title-task-full/test_resume_app.py", line 35, in setUp
    self.assertTrue(callable(getattr(self.app, "make_task", None)), "make_task is missing")
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: False is not true : make_task is missing

----------------------------------------------------------------------
Ran 2 tests in 0.001s

FAILED (failures=2)
```
green: `python -m unittest -v test_resume_app.MakeTaskTests`; exit status 0.
```text
test_exact_task_shape (test_resume_app.MakeTaskTests.test_exact_task_shape) ... ok
test_rejects_empty_titles (test_resume_app.MakeTaskTests.test_rejects_empty_titles) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.000s

OK
```
suite: `python -m unittest discover -v`; exit status 0.
```text
test_exact_task_shape (test_resume_app.MakeTaskTests.test_exact_task_shape) ... ok
test_rejects_empty_titles (test_resume_app.MakeTaskTests.test_rejects_empty_titles) ... ok
test_preserves_remaining_characters (test_resume_app.NormalizeTitleTests.test_preserves_remaining_characters) ... ok
test_rejects_empty_titles (test_resume_app.NormalizeTitleTests.test_rejects_empty_titles) ... ok
test_trims_boundary_whitespace (test_resume_app.NormalizeTitleTests.test_trims_boundary_whitespace) ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.001s

OK
```

## T003 execution evidence

red: `python -m unittest -v test_resume_app.CliTests`; exit status 1.
```text
test_invalid_arguments (test_resume_app.CliTests.test_invalid_arguments) ... 
  test_invalid_arguments (test_resume_app.CliTests.test_invalid_arguments) (args=()) ... FAIL
  test_invalid_arguments (test_resume_app.CliTests.test_invalid_arguments) (args=('',)) ... FAIL
  test_invalid_arguments (test_resume_app.CliTests.test_invalid_arguments) (args=(' \t\n ',)) ... FAIL
  test_invalid_arguments (test_resume_app.CliTests.test_invalid_arguments) (args=('\u2003\xa0',)) ... FAIL
  test_invalid_arguments (test_resume_app.CliTests.test_invalid_arguments) (args=('one', 'two')) ... FAIL
test_valid_titles (test_resume_app.CliTests.test_valid_titles) ... 
  test_valid_titles (test_resume_app.CliTests.test_valid_titles) (title='  Buy milk  ') ... FAIL
  test_valid_titles (test_resume_app.CliTests.test_valid_titles) (title='\u2003Café ☕\xa0') ... FAIL
  test_valid_titles (test_resume_app.CliTests.test_valid_titles) (title='  Café  ') ... FAIL
  test_valid_titles (test_resume_app.CliTests.test_valid_titles) (title=' MiXeD  interior\tspace ') ... FAIL

======================================================================
FAIL: test_invalid_arguments (test_resume_app.CliTests.test_invalid_arguments) (args=())
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/sp-sk-bridge-compat-ci/sp-sk-bridge-compat-ci/.runtime/latest-linux/projects/title-task-full/test_resume_app.py", line 82, in test_invalid_arguments
    self.assertEqual(result.returncode, 2, result.stderr)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 != 2 : 

======================================================================
FAIL: test_invalid_arguments (test_resume_app.CliTests.test_invalid_arguments) (args=('',))
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/sp-sk-bridge-compat-ci/sp-sk-bridge-compat-ci/.runtime/latest-linux/projects/title-task-full/test_resume_app.py", line 82, in test_invalid_arguments
    self.assertEqual(result.returncode, 2, result.stderr)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 != 2 : 

======================================================================
FAIL: test_invalid_arguments (test_resume_app.CliTests.test_invalid_arguments) (args=(' \t\n ',))
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/sp-sk-bridge-compat-ci/sp-sk-bridge-compat-ci/.runtime/latest-linux/projects/title-task-full/test_resume_app.py", line 82, in test_invalid_arguments
    self.assertEqual(result.returncode, 2, result.stderr)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 != 2 : 

======================================================================
FAIL: test_invalid_arguments (test_resume_app.CliTests.test_invalid_arguments) (args=('\u2003\xa0',))
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/sp-sk-bridge-compat-ci/sp-sk-bridge-compat-ci/.runtime/latest-linux/projects/title-task-full/test_resume_app.py", line 82, in test_invalid_arguments
    self.assertEqual(result.returncode, 2, result.stderr)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 != 2 : 

======================================================================
FAIL: test_invalid_arguments (test_resume_app.CliTests.test_invalid_arguments) (args=('one', 'two'))
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/sp-sk-bridge-compat-ci/sp-sk-bridge-compat-ci/.runtime/latest-linux/projects/title-task-full/test_resume_app.py", line 82, in test_invalid_arguments
    self.assertEqual(result.returncode, 2, result.stderr)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 != 2 : 

======================================================================
FAIL: test_valid_titles (test_resume_app.CliTests.test_valid_titles) (title='  Buy milk  ')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/sp-sk-bridge-compat-ci/sp-sk-bridge-compat-ci/.runtime/latest-linux/projects/title-task-full/test_resume_app.py", line 72, in test_valid_titles
    self.assertTrue(result.stdout.endswith("\n"), "JSON output needs a newline")
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: False is not true : JSON output needs a newline

======================================================================
FAIL: test_valid_titles (test_resume_app.CliTests.test_valid_titles) (title='\u2003Café ☕\xa0')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/sp-sk-bridge-compat-ci/sp-sk-bridge-compat-ci/.runtime/latest-linux/projects/title-task-full/test_resume_app.py", line 72, in test_valid_titles
    self.assertTrue(result.stdout.endswith("\n"), "JSON output needs a newline")
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: False is not true : JSON output needs a newline

======================================================================
FAIL: test_valid_titles (test_resume_app.CliTests.test_valid_titles) (title='  Café  ')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/sp-sk-bridge-compat-ci/sp-sk-bridge-compat-ci/.runtime/latest-linux/projects/title-task-full/test_resume_app.py", line 72, in test_valid_titles
    self.assertTrue(result.stdout.endswith("\n"), "JSON output needs a newline")
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: False is not true : JSON output needs a newline

======================================================================
FAIL: test_valid_titles (test_resume_app.CliTests.test_valid_titles) (title=' MiXeD  interior\tspace ')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/sp-sk-bridge-compat-ci/sp-sk-bridge-compat-ci/.runtime/latest-linux/projects/title-task-full/test_resume_app.py", line 72, in test_valid_titles
    self.assertTrue(result.stdout.endswith("\n"), "JSON output needs a newline")
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: False is not true : JSON output needs a newline

----------------------------------------------------------------------
Ran 2 tests in 0.103s

FAILED (failures=9)
```
green: `python -m unittest -v test_resume_app.CliTests`; exit status 0.
```text
test_invalid_arguments (test_resume_app.CliTests.test_invalid_arguments) ... ok
test_valid_titles (test_resume_app.CliTests.test_valid_titles) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.227s

OK
```
suite: `python -m unittest discover -v`; exit status 0.
```text
test_invalid_arguments (test_resume_app.CliTests.test_invalid_arguments) ... ok
test_valid_titles (test_resume_app.CliTests.test_valid_titles) ... ok
test_exact_task_shape (test_resume_app.MakeTaskTests.test_exact_task_shape) ... ok
test_rejects_empty_titles (test_resume_app.MakeTaskTests.test_rejects_empty_titles) ... ok
test_preserves_remaining_characters (test_resume_app.NormalizeTitleTests.test_preserves_remaining_characters) ... ok
test_rejects_empty_titles (test_resume_app.NormalizeTitleTests.test_rejects_empty_titles) ... ok
test_trims_boundary_whitespace (test_resume_app.NormalizeTitleTests.test_trims_boundary_whitespace) ... ok

----------------------------------------------------------------------
Ran 7 tests in 0.222s

OK
```

## Final review repair evidence

Important finding: option-shaped non-empty titles were parsed as options. Treat raw arguments as positional titles with an internal option terminator; arity remains enforced.

red: `python -m unittest -v test_resume_app.CliTests`; exit status 1.
```text
test_invalid_arguments (test_resume_app.CliTests.test_invalid_arguments) ... ok
test_valid_titles (test_resume_app.CliTests.test_valid_titles) ... 
  test_valid_titles (test_resume_app.CliTests.test_valid_titles) (title='-buy') ... FAIL
  test_valid_titles (test_resume_app.CliTests.test_valid_titles) (title='--help') ... ERROR
  test_valid_titles (test_resume_app.CliTests.test_valid_titles) (title='--') ... FAIL

======================================================================
ERROR: test_valid_titles (test_resume_app.CliTests.test_valid_titles) (title='--help')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/sp-sk-bridge-compat-ci/sp-sk-bridge-compat-ci/.runtime/latest-linux/projects/title-task-full/test_resume_app.py", line 75, in test_valid_titles
    task = json.loads(result.stdout)
  File "/opt/hostedtoolcache/Python/3.13.16/x64/lib/python3.13/json/__init__.py", line 352, in loads
    return _default_decoder.decode(s)
           ~~~~~~~~~~~~~~~~~~~~~~~^^^
  File "/opt/hostedtoolcache/Python/3.13.16/x64/lib/python3.13/json/decoder.py", line 345, in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
               ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.13.16/x64/lib/python3.13/json/decoder.py", line 363, in raw_decode
    raise JSONDecodeError("Expecting value", s, err.value) from None
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)

======================================================================
FAIL: test_valid_titles (test_resume_app.CliTests.test_valid_titles) (title='-buy')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/sp-sk-bridge-compat-ci/sp-sk-bridge-compat-ci/.runtime/latest-linux/projects/title-task-full/test_resume_app.py", line 73, in test_valid_titles
    self.assertEqual(result.returncode, 0, result.stderr)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 2 != 0 : usage: resume_app.py [-h] title
resume_app.py: error: the following arguments are required: title


======================================================================
FAIL: test_valid_titles (test_resume_app.CliTests.test_valid_titles) (title='--')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/sp-sk-bridge-compat-ci/sp-sk-bridge-compat-ci/.runtime/latest-linux/projects/title-task-full/test_resume_app.py", line 73, in test_valid_titles
    self.assertEqual(result.returncode, 0, result.stderr)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 2 != 0 : usage: resume_app.py [-h] title
resume_app.py: error: the following arguments are required: title


----------------------------------------------------------------------
Ran 2 tests in 0.313s

FAILED (failures=2, errors=1)
```
green: `python -m unittest -v test_resume_app.CliTests`; exit status 0.
```text
test_invalid_arguments (test_resume_app.CliTests.test_invalid_arguments) ... ok
test_valid_titles (test_resume_app.CliTests.test_valid_titles) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.300s

OK
```
green: `python -m unittest discover -v`; exit status 0.
```text
test_invalid_arguments (test_resume_app.CliTests.test_invalid_arguments) ... ok
test_valid_titles (test_resume_app.CliTests.test_valid_titles) ... ok
test_exact_task_shape (test_resume_app.MakeTaskTests.test_exact_task_shape) ... ok
test_rejects_empty_titles (test_resume_app.MakeTaskTests.test_rejects_empty_titles) ... ok
test_preserves_remaining_characters (test_resume_app.NormalizeTitleTests.test_preserves_remaining_characters) ... ok
test_rejects_empty_titles (test_resume_app.NormalizeTitleTests.test_rejects_empty_titles) ... ok
test_trims_boundary_whitespace (test_resume_app.NormalizeTitleTests.test_trims_boundary_whitespace) ... ok

----------------------------------------------------------------------
Ran 7 tests in 0.303s

OK
```

## T003 execution evidence

Completion continuation (2026-10-12): reused the actual independent review
retained in evidence/latest-linux/sessions/2026/10/12/rollout-2026-10-12T17-28-20-01a13128-7f34-7123-a627-ca35542f1a79.jsonl
and the existing final review repair evidence above. No new reviewer or product edits.

- Mandatory `$speckit-ci-post`: `python ci_hooks/record.py post` exited 0;
  root suite ran 7 tests, OK; reported suite_exit 0 and exit_code 0.
- Fresh verification: Python 3.13.16; `python -m unittest discover -v`
  ran 7 tests in 0.328s, OK, exit 0. `git diff --check` passed.
- Bridge guard allowed `superpowers:executing-plans`, status executing,
  pending tasks 0; canonical T001, T002, T003 remain checked.
- Branch finishing option 3 executed: kept `feature/title-task-full`;
  workspace preserved at
  /home/runner/work/sp-sk-bridge-compat-ci/sp-sk-bridge-compat-ci/.runtime/latest-linux/projects/title-task-full.
