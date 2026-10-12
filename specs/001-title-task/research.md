# Research: Title-to-task

Source: [approved PRD](../../docs/product/title-task-prd.md). No technical or product
unknowns remain; no external research or research delegation is needed.

- **Decision**: Use str.strip() and reject the empty result with ValueError.
  **Rationale**: Matches the approved Unicode whitespace and internal-content contract.
  **Alternatives considered**: ASCII-only trimming or collapsing spaces would violate the PRD.
- **Decision**: make_task calls normalization and returns exactly title and completed=False.
  **Rationale**: One source of validation preserves library/CLI consistency.
  **Alternatives considered**: Additional fields or independent normalization expand scope or risk drift.
- **Decision**: Use argparse for one required positional title, json.dumps for stdout,
  and convert blank-title ValueError to parser error (exit 2).
  **Rationale**: Standard-library parsing provides missing-title exit 2 without custom machinery.
  **Alternatives considered**: Manual argument parsing adds unnecessary error handling.
  Reject extra arguments, use default JSON formatting/escaping, and stderr diagnostics
  as builder choices permitted by the PRD; they do not extend the supported contract.
- **Decision**: Use unittest with subprocess.run and the active Python executable.
  **Rationale**: Direct tests verify dictionary types and exceptions; subprocess tests
  verify real JSON output, Unicode round-trip, and process exit codes.
  **Alternatives considered**: Third-party testing packages violate the dependency constraint.
- **Decision**: Retain three dependent implementation tasks and individual commits.
  **Rationale**: Approved workflow requires observed red/green evidence per task.
  **Alternatives considered**: Parallel implementation or a single task violates governance.
