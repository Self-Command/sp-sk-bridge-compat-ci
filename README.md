# Real Codex bridge compatibility tests

This public fixture tests unmodified Bridge 1.3.0 with Spec Kit 1.1.3 and Superpowers 7.0.0 using Codex CLI 0.162.1. The baseline is Spec Kit 1.0.12 and Superpowers 6.4.2. Every model process, including reviewers, must use `gpt-6.1-sol` via the Krill Responses endpoint.

The controller prepares disposable consumer repositories and invokes real `codex exec` processes. It does not execute the skills as a substitute for the tested model. Independent black-box checks, snapshots, JSONL events, bridge state and Git history determine results; a model's success claim is insufficient.

Trigger **Real Codex bridge compatibility** manually in Actions. Set repository secret `KRILL_API_KEY` first. Only sanitized fixture evidence is uploaded; credentials and Codex auth caches are excluded. Actions has read-only permissions and the model has no GitHub push credentials.

Model-call budgets: latest Linux 12, latest Windows 4, baseline Linux 4 (20 total); reviewers 6/3/3 (12 total). Each top-level call is limited to 20 minutes. These are invocation bounds, not API-request or monetary bounds. Token usage is reported when available.

The first Actions run completed one successful connection probe, then stopped on a controller snapshot error. That call counts against the 20-call budget; the repaired run permits 11 latest-Linux calls plus 4 Windows and 4 baseline calls. `prior-runs/38245424879-summary.json` preserves this accounting.

Scenarios cover actual SK document generation and automatic handoff, native SP execution/TDD/review/finishing, interruption and resume, mandatory post-hook failure, contradictory requirements, denied boundaries, drift, and next-feature archival. Latest Windows and old-version Linux use the same fixed product fixture for comparison. No upstream patches are applied to make tests pass.

The synthetic product interface is `python -m task_app --store PATH add TITLE`, `list`, `complete ID`, and `delete ID`, using JSON stdout and error exit code 2. It stores versioned JSON, validates 1–100 code-point titles, preserves data across reloads and rejects corrupt stores without overwriting them.

Reports distinguish pass, compatibility failure, and infrastructure blockage. Missing execution evidence is not a pass. Gateway model identity is reported only to the extent client/session/provider metadata can establish it.
