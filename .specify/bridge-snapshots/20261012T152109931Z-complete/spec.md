# Feature Specification: Title-to-task

**Feature Branch**: `feature/title-task-full`

**Created**: 2026-10-12

**Status**: Ready for planning

**Input**: Approved [PRD](../../docs/product/title-task-prd.md) and
[APPROVED_INPUTS.md](../../APPROVED_INPUTS.md).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create an incomplete task (Priority: P1)

An automation user supplies a title through the library or command line and
receives the same trimmed title in an incomplete task.

**Why this priority**: This is the fixture's entire user value.

**Independent Test**: Exercise each public surface with normal, Unicode, and blank titles.

**Acceptance Scenarios**:

1. **Given** `"  Buy milk  "`, **When** normalized, **Then** the title is `"Buy milk"`.
2. **Given** `"Buy  milk"`, **When** a task is created, **Then** internal double
   space remains and the task contains exactly title and completed=false.
3. **Given** `"  café 🚀  "`, **When** either task surface is used, **Then** the
   decoded title is `"café 🚀"`; command-line success exits 0.
4. **Given** an empty or whitespace-only title, **When** either library entry
   point is called, **Then** ValueError is raised; command-line use exits 2.
5. **Given** no command-line title, **When** invoked, **Then** exit is 2 and no
   successful task JSON is emitted.

### Edge Cases

Surrounding whitespace includes Unicode whitespace recognized by str.strip().
Internal whitespace and non-empty Unicode are preserved. Empty and whitespace-only
strings are rejected uniformly. Missing command-line title is an error.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: normalize_title(title) MUST strip surrounding string whitespace,
  preserve internal whitespace and Unicode, and raise ValueError for a blank result.
- **FR-002**: make_task(title) MUST use the same normalization and rejection,
  returning exactly `{"title": normalized_title, "completed": False}`.
- **FR-003**: `python resume_app.py TITLE` with one valid title MUST print the
  task as JSON with exactly title and completed (JSON false) and exit 0.
- **FR-004**: Empty, whitespace-only, or missing TITLE MUST exit 2 and MUST NOT
  emit successful task JSON.
- **FR-005**: Scope MUST exclude UI, database, network, installation, persistence,
  extra fields, and additional features.

### Key Entities *(include if feature involves data)*

- **Title**: A string whose surrounding whitespace is removed; the result is non-empty.
- **Task**: Exactly a normalized title and a completed flag initially false; no lifecycle
  updates or persistence are supported.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All five acceptance scenarios pass for their supported surfaces.
- **SC-002**: Both task surfaces produce identical decoded task values for every
  tested valid title, with exactly two fields and an incomplete status.
- **SC-003**: All tested blank titles are rejected; all tested valid Unicode titles
  survive trimming without changes to internal content.

## Assumptions

The PRD is authoritative and leaves no product questions. JSON key order,
formatting, Unicode escaping, error wording and diagnostic stream, extra CLI
arguments, and non-string library inputs remain builder discretion outside the
supported contract. There are no external services or stored data.
