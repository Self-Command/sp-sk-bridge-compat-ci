# Feature Specification: Title-to-task

**Feature Branch**: `feature/title-task-full`

**Created**: 2026-10-12

**Status**: Ready for planning

**Input**: Approved [PRD](../../docs/product/title-task-prd.md) and
[approved inputs](../../APPROVED_INPUTS.md); preserve their complete fixed scope.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Normalize a title (Priority: P1)
A caller obtains a non-empty title with surrounding whitespace removed.

**Why this priority**: Every task requires the same valid title.

**Independent Test**: Compare normalized ordinary and Unicode titles; reject empty titles.

**Acceptance Scenarios**:

1. **Given** `"  Buy milk  "`, **When** normalized, **Then** return `"Buy milk"`.
2. **Given** already normalized text, **When** normalized, **Then** preserve it.
3. **Given** `"  Café ☕  "`, **When** normalized, **Then** return `"Café ☕"`.
4. **Given** empty or whitespace-only text, **When** normalized, **Then** raise `ValueError`.

### User Story 2 - Create a task (Priority: P2)
A caller obtains a predictable incomplete task from a title.

**Why this priority**: The task shape enables automation.

**Independent Test**: Compare the complete returned object and invalid-title behavior.

**Acceptance Scenarios**:

1. **Given** `"  Buy milk  "`, **When** passed to `make_task`, **Then** return exactly
   `{"title": "Buy milk", "completed": false}` (boolean `False` in the library).
2. **Given** an invalid title, **When** creating a task, **Then** propagate `ValueError`.

### User Story 3 - Create a task from the command line (Priority: P3)
A user receives task JSON from a single quoted title argument.

**Why this priority**: Command output supports scripts.

**Independent Test**: Run the command and inspect decoded output and exit status.

**Acceptance Scenarios**:

1. **Given** a valid title, **When** running `python resume_app.py TITLE`, **Then** exit 0
   and print one JSON object followed by a newline, matching the library task.
2. **Given** missing, empty, whitespace-only, or extra positional arguments, **When** invoked,
   **Then** exit 2 and emit no task JSON on stdout.

### Edge Cases

- Whitespace means Python `str.strip()` semantics, including Unicode whitespace.
- Preserve interior whitespace, case, accents, emoji, and all remaining characters;
  do not normalize Unicode. Empty strings and `" \t\n "` are invalid.
- JSON key order and Unicode escaping are unspecified; decoded object equality is required.
- Error diagnostics may appear on stderr; wording is unspecified. Non-string library inputs
  are outside contract.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `resume_app.py` MUST expose `normalize_title(title)` accepting strings,
  stripping surrounding whitespace, preserving remaining text, and raising `ValueError` if empty.
- **FR-002**: `make_task(title)` MUST use the same validation and return a dictionary with
  exactly `title` and `completed`, normalized text and boolean `False` respectively.
- **FR-003**: The CLI MUST accept exactly one valid title, print the matching task as one JSON
  object plus newline, and exit 0.
- **FR-004**: Missing, empty, whitespace-only, or extra CLI arguments MUST exit 2 with no task JSON.
- **FR-005**: Non-empty Unicode titles MUST be accepted with the preservation rules above.
- **FR-006**: Scope MUST exclude UI, database, network, installation, persistence,
  additional features, and runtime dependencies.

### Key Entities *(include if feature involves data)*

- **Title**: Input string; after trimming must contain at least one character.
- **Task**: Exactly a normalized title and an incomplete boolean; no identity or lifecycle storage.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All seven PRD acceptance criteria pass with zero contract deviations.
- **SC-002**: Every valid documented title yields the same task through library and command line.
- **SC-003**: All four documented CLI invalid-input categories reject with exit 2 and no task JSON.

## Assumptions

- The PRD is authoritative; no unanswered product questions remain.
- Callers supply strings and quote CLI titles containing spaces. No external service is required.
- Execution governance and environment belong to the constitution and plan, not added product scope.
