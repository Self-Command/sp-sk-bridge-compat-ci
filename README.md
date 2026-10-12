# One small project: real Codex bridge test

Default workflow: **One small project - bridge smoke** (`bridge-smoke.yml`).

Fixed originals: Bridge 1.3.0, Spec Kit 1.1.3, Superpowers 7.0.0, Codex CLI 0.162.1.
Only `gpt-6.1-sol` via the Krill Responses endpoint. The fixed consumer project has
one task: implement `calculator.add(a,b)` and three standard-library unittest cases.

The controller prepares the canonical spec/plan/tasks. One real Codex invocation
reads the installed handoff command and Bridge skill, creates the handoff, adapts
T001 for native SP execution, applies TDD, reviews and keeps the feature branch.
It is limited to **one new top-level call, one short reviewer, low reasoning and
five minutes for the model process**. No SK design generation, platform matrix,
fault scenarios, recovery tests or second feature in the small test.

Independent checks inspect actual files, test failures and passes, the exact task
adapter, canonical checkbox, commit, branch and handoff completion. Success prose
does not count as evidence. Original installed skill bytes are hash-checked;
no upstream fixes are applied. All evidence is sanitized before upload.

Set Actions secret `KRILL_API_KEY`, then trigger `bridge-smoke.yml` manually.
The larger `compatibility.yml` is retained for reproducibility and disabled.

Prior runs are retained in `prior-runs/*-summary.json`. They used six top-level
calls and two reviewers in total; the last run verified SK generation and a real
automatic `after_tasks` handoff, then was canceled when the user narrowed scope
to a simple bridge test. Its incomplete execution is not a compatibility pass.
