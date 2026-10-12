"""Resume already archived second feature; three remaining bounded model calls."""
import json
import os
from pathlib import Path
import re
import shutil
import traceback

from fixtures import write
from run_suite import Suite
from sanitize import redact
from suite_verify import rows
from verify import digest


def main():
    prior=Path(os.environ['PRIOR_EVIDENCE'])/'latest-linux'
    suite=Suite();c=suite.c
    try:
        suite.setup()
        previous=json.loads((prior/'results.json').read_text(encoding='utf-8'))
        c.calls=previous['model_calls'];c.identities=set(previous['models_observed'])
        for p in (prior/'sessions').rglob('*.jsonl'):
            for line in p.read_text(encoding='utf-8').splitlines():
                event=json.loads(line);payload=event.get('payload',{})
                if event.get('type')=='response_item' and payload.get('type')=='function_call' and re.search(r'(?:^|[._])spawn_agent$',payload.get('name','')):
                    c.spawns.add(payload['call_id'])
        c.results=[r for r in previous['scenarios'] if r['name'] not in {
            'completed feature archival and next feature handoff','remaining fallback lifecycle',
            'installed upstream skills and bridge source remain original',
            'all four installed bridge skill entries consumed by real model'}]
        snapshot=prior/'04-next-feature-design/snapshot'
        # Text snapshots normalize CRLF. Original upstream release files must stay
        # those of the new native install; restore only actual consumer state.
        imported=[]
        for p in snapshot.rglob('*'):
            if not p.is_file():continue
            rel=p.relative_to(snapshot)
            if str(rel).replace('\\','/').startswith('.specify/extensions/speckit-superpowers-bridge/'):
                continue
            target=suite.root/rel;target.parent.mkdir(parents=True,exist_ok=True)
            mode=target.stat().st_mode if target.exists() else None
            shutil.copyfile(p,target)
            if mode is not None:target.chmod(mode)
            imported.append((rel,digest(p)))
        suite.hook_hashes={str(p.relative_to(suite.root)):digest(p) for p in (suite.root/'ci_hooks').glob('*.py')}
        suite.first_feature='specs/001-add-calculator'
        suite.first_code=(suite.root/'calculator.py').read_text(encoding='utf-8')
        archive=rows(suite.root/'.specify/bridge-events.jsonl')
        suite.check('archived second-feature snapshot resumed without changing upstream',{
            'consumer_files_identical':all(digest(suite.root/p)==sha for p,sha in imported),
            'archive_already_executed':any(x.get('action')=='archive' and x.get('feature_directory')==suite.first_feature for x in archive),
            'existing_subtraction_spec':(suite.feature()/'spec.md').exists()})
        c.command('second-product-import-add',['git','add','.'],suite.root)
        c.command('second-product-import-commit',['git','commit','-m','test: resume actual generated second feature with original installed release'],suite.root)
        suite.call('04b-scope-plan-tasks',suite.root,'''Resume the already-created
second feature specs/002-subtract-calculator; do not archive or specify it again.
The user has authorized complete testing of every bridge entry. This exact
test-scope amendment is APPROVED: preserve existing add(a,b) and its three tests,
allow subtract(a,b) returning integer a-b, and exactly three additional unittest
cases (2,3)->-1, (-2,2)->-4, (0,0)->0. No other requirements change.
Use $speckit-constitution to apply only that narrow scope amendment, preserving
all TDD, dependency, commit and branch principles. This is the approval the prior
session needed; do not stop to request it again. Then use $speckit-plan,
$speckit-tasks and $speckit-analyze, honoring mandatory automatic hooks.
Prefer one cohesive code/test task, native template sections short. Stop before
application code. No reviewers in this design call. Keep existing branch.
''',300)
        state=c.state(suite.root);feature=str(suite.feature().relative_to(suite.root))
        valid=suite.check('second feature scope amendment plan tasks and automatic handoff',{
            'new_feature_pointer':feature!=suite.first_feature,
            'real_archive_event_retained':any(x.get('action')=='archive' and x.get('feature_directory')==suite.first_feature for x in archive),
            'new_handoff_ready':state.get('status')=='ready' and state.get('feature_directory')==feature,
            'prior_add_code_preserved':(suite.root/'calculator.py').read_text(encoding='utf-8')==suite.first_code,
            'new_plan_and_tasks':all((suite.feature()/name).exists() for name in ['plan.md','tasks.md'])})
        if valid:suite.fallback_and_recovery()
        else:c.record('remaining execute and recovery','blocked','Real second-feature prerequisites still failed')
    except Exception as exc:
        write(c.evidence/'resume-error.log',redact(traceback.format_exc()))
        c.record('resume infrastructure or controller','blocked',str(exc))
    if (prior/'sessions').exists():shutil.copytree(prior/'sessions',c.evidence/'sessions/prior-run-38255807767',dirs_exist_ok=True)
    write(c.evidence/'resume.json',json.dumps({
        'source_run':'https://github.com/Self-Command/sp-sk-bridge-compat-ci/actions/runs/38255807767',
        'original_run':'https://github.com/Self-Command/sp-sk-bridge-compat-ci/actions/runs/38253965707',
        'earlier_suite_calls':5,'earlier_suite_reviewers':1,
        'upstream_import_note':'Prior text evidence normalized CRLF. Release files were restored from the native unchanged pinned installation; only consumer state was imported.',
        'scope_approval_note':'Explicit authorized test-scope amendment resolves a generated addition-only constitution; no new feature outside calculator test fixture.'},indent=2))
    return suite.finish()


if __name__=='__main__':
    raise SystemExit(main())
