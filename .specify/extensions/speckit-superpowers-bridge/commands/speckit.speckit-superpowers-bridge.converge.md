---
description: "Assess an SP-completed feature using the installed SK convergence procedure"
---

# Bridge Converge

Use this entry after Superpowers has completed the active Spec Kit feature.
It delegates assessment and append-only task generation to the installed
Spec Kit convergence instructions through a disposable compatibility adapter.
The original `$speckit-converge` / `/speckit-converge` remains unchanged and still
requires SK implement; never claim that SK implement ran when SP implemented.

## Procedure

1. Stay in the consumer repository. **Do not auto-archive the completed handoff**:
   its feature identity, hashes and events qualify this assessment.
2. Run the helper selected by `.specify/init-options.json.script` and the active
   agent (`codex` or `claude`). Read its JSON and exit code:

   ```powershell
   .\.specify\extensions\speckit-superpowers-bridge\scripts\powershell\prepare-convergence.ps1 -Actor <codex|claude>
   ```

   ```bash
   bash .specify/extensions/speckit-superpowers-bridge/scripts/bash/prepare-convergence.sh --actor <codex|claude>
   ```

   The helper requires complete SP handoff, a matching executing/completion
   event sequence and snapshot, matching artifact hashes, source-of-truth paths,
   active feature and completed non-deferred canonical tasks. It writes only a
   unique OS-temporary adapter. If it exits nonzero or `eligible` is false,
   report `reason` and STOP without changing the consumer. Do not repair evidence,
   change checkboxes, run SK implement or bypass a failed prerequisite.
3. Read `adapter_path` in full and execute that procedure **within this bridge
   command**. Its only text adaptations are the truthful verified-SP prerequisite
   and the follow-up executor reference. Do not invoke the unadapted native skill,
   replace its assessment algorithm or modify any installed skill file.
4. Run the feature's documented verification commands and inspect their actual
   results alongside the implementation. A failing product test is evidence for
   the native findings assessment, not permission to fix code in this command.
5. Honor every native step, including before/after convergence hooks, finding
   classification, requirements/constitution checks, severity, append-only task
   rules and next-ID calculation. Actually invoke and await mandatory hooks;
   keep optional, disabled, conditional and malformed-registry behavior identical
   to the installed native procedure. A mandatory hook failure stops execution.
6. On `converged`, leave spec.md, plan.md, tasks.md and application files unchanged
   and retain the completed handoff. On `tasks_appended`, append only the native
   traceable corrective tasks, then use the existing platform `update-handoff`
   script with ready and the active actor. Re-read the resulting JSON: exit 0
   alone does not establish ready. Return the pending tasks to
   `$speckit-superpowers-bridge` (Codex) or `/speckit-superpowers-bridge` (Claude).
   Do not run implementation automatically from a convergence request.
7. If a mandatory before/after convergence hook fails, use `update-handoff` with
   blocked, the active actor and a reason naming the hook. Preserve any tasks
   already appended; never roll back task history or report clean completion.
   After fixing the hook, re-establish verified completion through the bridge
   before requesting convergence again.
8. Remove the helper-created adapter file in all exit paths. Summarize the native
   assessment result and provide the actual evidence/next command. No adapter
   becomes a tracked skill, permanent plan or second completion contract.
