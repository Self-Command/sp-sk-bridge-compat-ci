# Original-release full bridge coverage

Workflow: **Original bridge full coverage - Codex Linux Windows** (`bridge-full.yml`).
Pinned Bridge 1.3.0 / SK 1.1.3 / SP 7.0.0 / Codex CLI 0.162.1, gpt-6.1-sol low.
Linux runs first (at most 14 controller calls / 4 review agents), then Windows
(at most 6 / 2), including failures and retries: 20 / 6 in total. Native files
are hash-checked and never patched. Known original-release failures remain failures.

The three-task title-to-task JSON fixture exercises native SP brainstorming and
builder check, PRD-to-SK constitution/spec/clarify/plan/tasks/checklist/analyze,
automatic handoff, SP TDD/execution/review/verification/finishing, and actual
canonical task progress. Linux adds committed-task interruption with a native
completion ledger, injected product-fault debugging, pre/post hook failures,
fresh-session recovery, review remediation/re-review, hook registry variants,
all four bridge entries, missing spec/plan/tasks, conflict blocking, native
converge prerequisites, official GitHub MCP issue creation/deduplication, and
worktree/local-merge/PR integration. Windows independently generates and completes
the same main flow and checks the PowerShell protocol scripts.

Only the test repository receives synthetic issues and `full-ci/<run>/...`
branches. Existing policies that prohibit PR creation are reported as blocked;
the runner never changes repository policies. The original `converge` contract
is not waived when it requires SK implement. No agent/platform extrapolation.

Run `python -m unittest discover -s tests -v` before dispatch. Evidence reports
pass, fail, blocked and not_covered separately. Exported rollouts, commands,
snapshots, independent checks and token counts are sanitized before upload.
The historical calculator suite below remains available and unchanged in scope.

# Complete small-project bridge validation

Primary workflow: **Complete small project - all bridge skills** (`bridge-complete.yml`).
Pinned originals: Bridge 1.3.0, Spec Kit 1.1.3, Superpowers 7.0.0, Codex CLI 0.162.1.
Only `gpt-6.1-sol` through Krill Responses, with low reasoning for all calls and reviewers.

The model generates SK constitution/spec/plan/tasks and performs analysis, automatic
handoff, native SP execution/TDD/review/verification/finishing, and canonical progress.
One calculator project first adds `add` via the normal alias, then adds `subtract`
via the canonical execute entry after completed-feature archival. Each has three
stdlib unittest cases. Mandatory pre/post hooks are genuinely invoked; an intentional
post-hook failure must prevent completion, followed by fresh-session recovery.
Protocol fixtures call the standalone handoff and guard entries, cover all five guard
rules, missing design files, requirements conflict and read-only readiness.

Normal run: seven top-level calls, hard limit eight, at most two reviewers.
Independent checks inspect actual files, runtime-injected skill messages, command exits,
ordered test failures/passes, hook markers, task adapters and handoff events. Any failed
or blocked check fails the Actions job. Original skills and scripts remain unchanged.
Evidence is sanitized and uploaded as `complete-bridge-evidence`, including a report
and usage counts from both main and reviewer sessions. This workflow runs on Linux;
other platforms and agents are not inferred to pass.

Set repository secret `KRILL_API_KEY` and manually dispatch `bridge-complete.yml`.
Previous smoke evidence and the disabled larger matrix are retained below.

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
