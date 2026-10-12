"""The eighth and final suite call: recover the real post-hook-failure state."""
import json
import os
from pathlib import Path
import re
import shutil
import sys
import traceback

from continue_suite import artifacts
from fixtures import write
from run_suite import Suite
from sanitize import redact
from suite_verify import preserved_contracts, rows
from verify import digest, tasks


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
            '05-fallback-execute product and SP discipline','fresh-session recovery',
            'installed upstream skills and bridge source remain original',
            'all four installed bridge skill entries consumed by real model'}]
        snapshot=prior/'05-fallback-execute/snapshot'
        before=artifacts(prior/'04b-scope-plan-tasks/snapshot');after=artifacts(snapshot)
        original=json.loads((prior/'05-fallback-execute/external-checks.json').read_text())
        original['canonical_requirements_preserved']=all(preserved_contracts(before,after).values())
        suite.check('05-fallback-execute product and SP discipline rechecked',original,
                    correction='Task explicitly requested red/green results in tasks.md; only a progress sentence, checkbox and required evidence changed.')
        if not all(original.values()):raise RuntimeError('Fallback product verification still fails')
        for p in snapshot.rglob('*'):
            if not p.is_file():continue
            rel=p.relative_to(snapshot)
            if str(rel).replace('\\','/').startswith('.specify/extensions/speckit-superpowers-bridge/'):continue
            target=suite.root/rel;target.parent.mkdir(parents=True,exist_ok=True)
            mode=target.stat().st_mode if target.exists() else None
            shutil.copyfile(p,target)
            if mode is not None:target.chmod(mode)
        suite.hook_hashes={str(p.relative_to(suite.root)):digest(p) for p in (suite.root/'ci_hooks').glob('*.py')}
        state=c.state(suite.root);feature=state['feature_directory']
        hookrows=[x for x in rows(suite.root/'.specify/ci-hook-events.jsonl') if x.get('feature')==feature]
        if state.get('status')!='executing' or not any(x.get('forced_failure') and x.get('exit_code')==23 for x in hookrows):
            raise RuntimeError('Not the actual failed post-hook state')
        if len(c.spawns)!=2:raise RuntimeError('Both original code reviews are not accounted for')
        (suite.root/'ci_hooks/FAIL_POST').unlink(missing_ok=True)
        code_before={str(p.relative_to(suite.root)):digest(p) for p in [suite.root/'calculator.py',*sorted((suite.root/'tests').glob('*.py'))]}
        c.command('recovery-product-add',['git','add','.'],suite.root)
        c.command('recovery-product-commit',['git','commit','-m','test: resume real failed hook after external fixture repair'],suite.root)
        suite.call('06-fresh-session-recovery',suite.root,'''$speckit-superpowers-bridge
Fresh-session recovery of the exact completed subtraction feature that stopped
on mandatory ci-post hook exit 23. The operator removed only the external FAIL_POST
flag. All canonical tasks are checked; both addition and subtraction already had
actual independent gpt-6.1-sol reviews with no material findings. Reuse those
reviews; DO NOT spawn any reviewer or repeat completed tasks. Read existing
handoff, rerun the mandatory post-hook via its installed rendered hook skill,
freshly verify all six unittest cases and finish choice 3 (keep branch).
Set complete only after the mandatory post-hook really succeeds. Never rewrite
code/tests, installed skills/scripts or product requirements. Stop after completion.
''',180)
        state=c.state(suite.root)
        later=rows(suite.root/'.specify/ci-hook-events.jsonl')[len(rows(snapshot/'.specify/ci-hook-events.jsonl')):]
        external=c.command('final-independent-behavior',[sys.executable,'-c',
            'import calculator as c; assert [c.add(2,3),c.add(-2,2),c.add(0,0)]==[5,0,0]; assert [c.subtract(2,3),c.subtract(-2,2),c.subtract(0,0)]==[-1,-4,0]; print("Six independently checked behaviors pass")'],suite.root,check=False)
        tests_result=c.command('final-independent-unittest',[sys.executable,'-m','unittest','discover','-s','tests','-v'],suite.root,check=False)
        suite.check('fresh-session recovery without repeating completed code',{
            'handoff_complete':state.get('status')=='complete',
            'all_tasks_checked':all(t[1] for t in tasks(suite.feature()/'tasks.md')),
            'code_tests_unchanged':all(digest(suite.root/p)==sha for p,sha in code_before.items()),
            'both_reviews_reused_without_new_spawn':len(c.spawns)==2,
            'mandatory_posthook_success_before_complete':any(x['phase']=='post' and x['exit_code']==0 and x['status_before']=='executing' for x in later),
            'six_external_behaviors_pass':external.returncode==0,
            'six_unittest_cases_pass':tests_result.returncode==0 and 'Ran 6 tests' in tests_result.stderr})
    except Exception as exc:
        write(c.evidence/'recovery-error.log',redact(traceback.format_exc()))
        c.record('final recovery infrastructure or controller','blocked',str(exc))
    if (prior/'sessions').exists():shutil.copytree(prior/'sessions',c.evidence/'sessions/prior-run-38256610954',dirs_exist_ok=True)
    write(c.evidence/'recovery.json',json.dumps({'source_run':'https://github.com/Self-Command/sp-sk-bridge-compat-ci/actions/runs/38256610954',
        'prior_suite_calls':7,'prior_reviewers':2,'new_call_limit':1,
        'repair':'Removed only intentional external ci_hooks/FAIL_POST flag. Upstream release unmodified. Canonical task requirements preserved.'},indent=2))
    return suite.finish()


if __name__=='__main__':
    raise SystemExit(main())
