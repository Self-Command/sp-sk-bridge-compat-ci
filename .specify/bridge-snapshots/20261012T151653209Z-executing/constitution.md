<!-- Sync Impact Report: scaffold → 1.0.0; five principles established;
added Scope Constraints and Development Workflow; removed none; no deferred TODOs. -->
# Title-to-task Constitution

## Core Principles

### I. Approved Contract
All behavior MUST preserve the approved [PRD](../../docs/product/title-task-prd.md)
and APPROVED_INPUTS.md: public interfaces, Unicode and empty-title rules,
exact task fields, and CLI exit codes. Scope MUST NOT expand.

### II. Standard Library Only
Python 3.13 and standard-library unittest MUST be used. No runtime dependencies,
installation, UI, database, network, or persistence are permitted.

### III. Observed Test-First Development
Each behavior MUST begin with a unittest that is run and observed failing for
that missing behavior before implementation. Then run and record passing tests;
refactoring MUST preserve green results. Approval for these tests is already supplied.

### IV. Three Dependent Tasks
Implementation MUST contain exactly three cohesive tasks: T001 normalize_title
and tests; T002 make_task and tests, depending on T001; T003 CLI and tests,
depending on T001 and T002. Each task MUST have its own commit containing its
canonical checkbox update and actual execution evidence.

### V. Canonical Spec Kit Ownership
Only Spec Kit MUST produce canonical spec, plan, and tasks. The model executes
product work; bridge guards MUST run when installed and mandatory. Guard failure
MUST stop completion. Installed skills, bridge release files, CI hooks, and external
controls MUST NOT be modified.

## Scope Constraints
The library and CLI MUST live in resume_app.py and expose normalize_title(title),
make_task(title), and python resume_app.py TITLE. Builder discretion is limited
to the PRD's explicitly unspecified details.

## Development Workflow
Design precedes task generation and implementation. Keep the feature branch
(finish option 3); do not merge or publish. No application code, tests, scaffolding,
or tasks are generated during the current constitution/specification/planning stage.
Verify governance before and after design, and verify actual tests before claiming
implementation success.

## Governance
This constitution governs the fixed fixture. Amendments require explicit approved
requirements and a documented impact review. Use semantic versioning: major for
incompatible governance changes, minor for new rules, patch for clarifications.
Every design and implementation review MUST verify these principles.

**Version**: 1.0.0 | **Ratified**: 2026-10-12 | **Last Amended**: 2026-10-12
