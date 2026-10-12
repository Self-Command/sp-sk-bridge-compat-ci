#!/usr/bin/env bash
# Qualify SP completion and adapt only the installed SK executor seam.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/common-actor-resolution.sh"
. "$SCRIPT_DIR/bridge-state.sh"
NATIVE_COMMAND=""
ACTOR=""
while [ "$#" -gt 0 ]; do
    case "$1" in
        --native-command) NATIVE_COMMAND="${2:-}"; shift 2 ;;
        --actor) ACTOR="${2:-}"; shift 2 ;;
        *) printf 'Usage: prepare-convergence.sh [--native-command PATH] [--actor codex|claude]\n' >&2; exit 2 ;;
    esac
done
command -v jq >/dev/null 2>&1 || { printf 'Missing dependency: jq\n' >&2; exit 1; }
refuse() {
    jq -nc --arg reason "$1" '{eligible:false,reason:$reason}'
    exit 1
}
ROOT="$(get_repo_root)"
ACTOR="$(resolve_bridge_actor "$ACTOR")"
ROOT="$(cd "$ROOT" && pwd -P)"
HANDOFF="$ROOT/.specify/superpowers-handoff.json"
[ -f "$HANDOFF" ] || refuse 'Missing completed Superpowers handoff.'
jq -e '.status == "complete" and .executor == "superpowers" and (.feature_directory | type == "string" and length > 0)' "$HANDOFF" >/dev/null 2>&1 || refuse 'Convergence requires a completed Superpowers handoff with a feature directory.'
FEATURE="$(jq -r '.feature_directory' "$HANDOFF")"
[[ "$FEATURE" != /* ]] || refuse 'The completed feature must be inside this repository.'
FEATURE_FULL="$(cd "$ROOT/$FEATURE" 2>/dev/null && pwd -P)" || refuse 'The completed feature directory does not exist.'
case "$FEATURE_FULL" in "$ROOT"/*) ;; *) refuse 'The completed feature must be inside this repository.' ;; esac
if [ -f "$ROOT/.specify/feature.json" ]; then
    CURRENT="$(jq -r '.feature_directory // empty' "$ROOT/.specify/feature.json" 2>/dev/null)" || refuse 'Invalid active feature pointer.'
    if [ -n "$CURRENT" ]; then
        if [[ "$CURRENT" = /* ]]; then CURRENT_FULL="$(cd "$CURRENT" 2>/dev/null && pwd -P)" || refuse 'Active feature pointer does not match the completion.'
        else CURRENT_FULL="$(cd "$ROOT/$CURRENT" 2>/dev/null && pwd -P)" || refuse 'Active feature pointer does not match the completion.'; fi
        [ "$CURRENT_FULL" = "$FEATURE_FULL" ] || refuse 'Active feature pointer does not match the completion.'
    fi
fi
for artifact in spec.md plan.md tasks.md; do
    [ -f "$FEATURE_FULL/$artifact" ] || refuse "Missing required Spec Kit artifact: $artifact."
    key="${artifact%.md}"
    pointer="$(jq -r --arg key "$key" '.source_of_truth[$key] // empty' "$HANDOFF")"
    [ "$pointer" = "$FEATURE/$artifact" ] || refuse "Source-of-truth pointer mismatch: $artifact."
    stored="$(jq -r --arg name "$artifact" '.artifacts_sha256[$name] // empty' "$HANDOFF")"
    [[ "$stored" =~ ^[0-9a-f]{64}$ ]] || refuse "Missing completion artifact hash: $artifact."
    [ "$stored" = "$(compute_artifact_sha256 "$FEATURE_FULL/$artifact")" ] || refuse "Artifact changed since completion: $artifact."
done
[ "$(get_pending_task_count "$FEATURE_FULL/tasks.md")" -eq 0 ] || refuse 'Non-deferred tasks remain pending; execute them through the bridge first.'
grep -Eq '^- \[[ xX]\] T[0-9]+' "$FEATURE_FULL/tasks.md" || refuse 'The task contract has no canonical task IDs.'
EVENTS="$ROOT/.specify/bridge-events.jsonl"
[ -f "$EVENTS" ] || refuse 'Missing Superpowers execution/completion events.'
SNAPSHOT="$(jq -r '.last_snapshot_id // empty' "$HANDOFF")"
[ -n "$SNAPSHOT" ] || refuse 'Missing completion snapshot identity.'
jq -se --arg feature "$FEATURE" --arg snapshot "$SNAPSHOT" '
    [.[] | select(.action == "handoff" and .feature_directory == $feature)] as $events
    | ($events | length) >= 2
      and $events[-1].status == "complete"
      and $events[-1].snapshot_id == $snapshot
      and any($events[0:-1][]; .status == "executing")
' "$EVENTS" >/dev/null 2>&1 || refuse 'No matching executing-to-complete event sequence for this snapshot.'
if [ -z "$NATIVE_COMMAND" ]; then
    case "$ACTOR" in
        codex) NATIVE_COMMAND="$ROOT/.agents/skills/speckit-converge/SKILL.md" ;;
        claude) NATIVE_COMMAND="$ROOT/.claude/skills/speckit-converge/SKILL.md" ;;
        *) refuse 'Select --actor codex or claude, or provide --native-command.' ;;
    esac
fi
[ -f "$NATIVE_COMMAND" ] || refuse 'Installed native SK converge command not found.'
# The narrow two-line seam is deliberately recognized before any replacement.
native="$(cat "$NATIVE_COMMAND"; printf '.')"
native="${native%.}"
native="${native//$'\r'/}"
if [[ "$native" = *'`$speckit-implement`'* ]]; then
    implement='`$speckit-implement`'; tasks='`$speckit-tasks`'; bridge='`$speckit-superpowers-bridge`'
elif [[ "$native" = *'`/speckit-implement`'* ]]; then
    implement='`/speckit-implement`'; tasks='`/speckit-tasks`'; bridge='`/speckit-superpowers-bridge`'
else refuse 'Unrecognized native SK converge executor contract; no adapter created.'; fi
old="This command MUST run only after
$implement has run on the current \`tasks.md\`, and after $tasks has produced a complete \`tasks.md\`."
[[ "$native" = *"$old"* && "$native" = *'APPEND-ONLY, NEVER REWRITE'* && "$native" = *'### 9. Check for extension hooks'* ]] || refuse 'Unrecognized native SK converge procedure; no adapter created.'
new="This bridge adapter MUST run only after verified Superpowers completion of the current \`tasks.md\`, and after $tasks has produced a complete \`tasks.md\`."
adapted="${native/"$old"/"$new"}"
adapted="${adapted//"$implement"/"$bridge"}"
ADAPTER="$(mktemp "${TMPDIR:-/tmp}/speckit-bridge-converge.XXXXXX")"
printf '%s' "$adapted" > "$ADAPTER"
jq -nc --arg feature "$FEATURE" --arg path "$ADAPTER" --arg source_sha256 "$(compute_artifact_sha256 "$NATIVE_COMMAND")" \
    '{eligible:true,feature_directory:$feature,adapter_path:$path,source_sha256:$source_sha256}'
