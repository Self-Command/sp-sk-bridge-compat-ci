<!-- Sync Impact Report: scaffold → 1.0.0 (initial ratification).
Principles: five placeholders → Contract fidelity, Standard library, Observed TDD,
Dependent task commits, Canonical ownership. Added: Scope constraints, Workflow.
Removed: scaffold examples. Follow-up TODOs: none. -->
# Title-to-task Constitution

## Core Principles

### I. Contract Fidelity
The implementation MUST preserve every interface, Unicode/empty rule, exact task shape,
and exit code in docs/product/title-task-prd.md. Non-string library inputs are outside contract.

### II. Standard Library Only
The fixture MUST use Python 3.13 and only its standard library; tests MUST use unittest.
This keeps the compatibility fixture self-contained.

### III. Observed TDD
For each implementation task, tests MUST be written first and run to observe failure before
implementation. The same tests MUST then pass; retain actual command/output evidence.
Approved inputs authorize the test cases; never fabricate red/green results.

### IV. Dependent Task Commits
Future canonical tasks MUST be exactly three: T001 normalization and tests; T002 task creation
and tests depending on T001; T003 CLI and tests depending on T001 and T002.
Each task MUST have its own commit containing its canonical completed checkbox and actual
execution evidence. No implementation or tasks are generated during this design invocation.

### V. Canonical Spec Kit Ownership
Only Spec Kit MUST produce canonical spec.md, plan.md, and tasks.md. Mandatory installed
hooks MUST execute successfully before proceeding. Model product work MUST use gpt-6.1-sol;
this invocation permits no reviewer spawns. Keep the feature branch (finish option 3).

## Scope Constraints
No UI, database, network, installation, persistence, additional features, or runtime dependencies.
APPROVED_INPUTS.md and docs/product/title-task-prd.md are the approved pre-spec inputs.

## Development Workflow
Design precedes task generation and implementation. Future execution MUST respect task
ordering, observed TDD, and per-task commits. Validation MUST cover library boundaries and
CLI subprocess output/exit status. Do not merge, push, or delete the feature branch.

## Governance
This constitution governs feature artifacts. Amendments require explicit user authorization,
a recorded rationale, and a compliance check against affected artifacts. Use semantic versioning:
major for incompatible principles, minor for new guidance, patch for clarifications.
Check compliance before planning and again after design; stop on unjustified violations.

**Version**: 1.0.0 | **Ratified**: 2026-10-12 | **Last Amended**: 2026-10-12
