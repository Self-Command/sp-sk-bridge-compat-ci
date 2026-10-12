# Research: Title-to-task

Source: [approved PRD](../../docs/product/title-task-prd.md). No unknowns remain;
local approved inputs fully determine the design, so no research agents are needed.

- **Decision**: Use Python 3.13 str.strip() for normalization.
  **Rationale**: Exactly matches the approved ordinary and Unicode whitespace contract.
  **Alternatives considered**: ASCII-only trimming or Unicode normalization would change behavior.
- **Decision**: make_task delegates validation to normalize_title and returns only two keys.
  **Rationale**: Library and CLI must share the same title and incomplete boolean.
  **Alternatives considered**: Independent validation risks divergence; additional metadata is out of scope.
- **Decision**: Use argparse for one positional title and json for one object plus newline.
  Catch invalid-title ValueError and report an argument error with exit 2.
  **Rationale**: Standard library handles missing/extra arguments; the same exit code covers emptiness.
  **Alternatives considered**: Manual argument counting is possible but adds avoidable parsing logic.
- **Decision**: Use unittest and subprocess with the active Python executable.
  **Rationale**: Direct tests verify library contracts; subprocesses verify actual streams and exit codes.
  **Alternatives considered**: Third-party runners violate the approved dependency constraint.
- **Decision**: Require observed red/green evidence and separate future task commits.
  **Rationale**: Constitution mandates execution proof for three dependent tasks.
  **Alternatives considered**: Unobserved tests or a single combined commit violate governance.
