# Authorized full compatibility test
Only gpt-6.1-sol and low reasoning for main agent and every reviewer. Read this
file first. At most the explicitly stated number of review agents; no implementer
agents. Specify model="gpt-6.1-sol", reasoning_effort="low", fork_turns="none".
The entire fixed title-task scope in APPROVED_INPUTS.md and scripted testing
answers are approved. This is an isolated disposable checkout. Use this checkout
unless BRANCH_CASES.md explicitly authorizes creating its test worktrees.
Use standard-library unittest and observed red/green tests. No new features.
Only SK produces canonical spec/plan/tasks; only model executes product work.
Never modify installed skills, bridge release files, ci_hooks scripts, or the
external controller/verifier. Do not print credentials or inspect auth files.
Optional hooks: accept ci-accepted, decline ci-declined. Nonempty conditions
belong to upstream and must be skipped. Fault flags are external controls:
never remove or rewrite them. Mandatory hook failure stops completion.
Keep the feature branch by default. Only BRANCH_CASES.md may authorize a local
merge or push/PR into its specifically named test branches; never merge to main.
Read required skills once, keep outputs concise and use actual tool evidence.
