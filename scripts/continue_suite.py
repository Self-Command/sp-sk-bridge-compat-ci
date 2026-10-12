"""Continue the exact generated product snapshot; no repeated design/addition calls."""
import json
import os
from pathlib import Path
import re
import shutil
import traceback

from fixtures import write
from run_suite import Suite
from sanitize import redact
from suite_verify import preserved_contracts, injected_skills
from verify import digest


def artifacts(root):
    paths=[root/'.specify/memory/constitution.md',*sorted((root/'specs').glob('*/*.md'))]
    return {str(p.relative_to(root)).replace('\\','/'):p.read_text(encoding='utf-8') for p in paths if p.exists()}


def main():
    prior=Path(os.environ['PRIOR_EVIDENCE'])/'latest-linux'
    suite=Suite();c=suite.c
    try:
        # This is an explicit continuation: four top-level calls and one reviewer
        # already happened in run 38253965707. Both remain in the same suite budget.
        suite.setup()
        previous=json.loads((prior/'results.json').read_text(encoding='utf-8'))
        c.calls=previous['model_calls']
        c.identities=set(previous['models_observed'])
        for p in (prior/'sessions').rglob('*.jsonl'):
            for line in p.read_text(encoding='utf-8').splitlines():
                event=json.loads(line);payload=event.get('payload',{})
                if event.get('type')=='response_item' and payload.get('type')=='function_call' and re.search(r'(?:^|[._])spawn_agent$',payload.get('name','')):
                    c.spawns.add(payload['call_id'])
        c.results=[r for r in previous['scenarios'] if r['name'] not in {
            '03-alias-execute product and SP discipline','remaining project lifecycle',
            'all four installed bridge skill entries consumed by real model'}]
        snapshot=prior/'03-alias-execute/snapshot'
        old=artifacts(prior/'02-tasks-analysis/snapshot');new=artifacts(snapshot)
        checks=preserved_contracts(old,new)
        original=json.loads((prior/'03-alias-execute/external-checks.json').read_text())
        original['canonical_requirements_preserved']=all(checks.values())
        suite.check('03-alias-execute product and SP discipline rechecked',original,
                    correction='Original SK task explicitly required append-only T001 execution evidence in tasks.md; its canonical contract is unchanged.',
                    preserved=checks,original_run='38253965707')
        if not all(original.values()):raise RuntimeError('Imported first product is not externally verified')
        script_modes={str(p.relative_to(suite.root)):p.stat().st_mode for p in (suite.root/'.specify').rglob('*.sh')}
        shutil.copytree(snapshot,suite.root,dirs_exist_ok=True)
        # Actions text artifacts do not preserve Unix executable permissions.
        # Restore the fresh native installation modes without changing bytes.
        for relative,mode in script_modes.items():
            (suite.root/relative).chmod(mode)
        state=c.state(suite.root)
        if state.get('status')!='complete':raise RuntimeError('Real imported handoff is not complete')
        suite.first_feature=state['feature_directory']
        suite.first_code=(suite.root/'calculator.py').read_text(encoding='utf-8')
        suite.hook_hashes={str(p.relative_to(suite.root)):digest(p) for p in (suite.root/'ci_hooks').glob('*.py')}
        c.command('imported-product-add',['git','add','.'],suite.root)
        c.command('imported-product-commit',['git','commit','-m','test: preserve actual first-run product for bridge continuation'],suite.root)
        suite.check('actual product resumed from prior Actions artifact',{
            'all_snapshot_files_identical':all(digest(suite.root/p.relative_to(snapshot))==digest(p) for p in snapshot.rglob('*') if p.is_file()),
            'handoff_really_complete':c.state(suite.root).get('status')=='complete'})
        if suite.second_feature():suite.fallback_and_recovery()
        else:c.record('remaining fallback lifecycle','blocked','Second feature generation or handoff failed')
    except Exception as exc:
        write(c.evidence/'continuation-error.log',redact(traceback.format_exc()))
        c.record('continuation infrastructure or controller','blocked',str(exc))
    # Preserve all previous runtime-injected skills, usage and full evidence. Do
    # not replace the original failure report or its logs with corrected claims.
    if (prior/'sessions').exists():shutil.copytree(prior/'sessions',c.evidence/'sessions/prior-run-38253965707',dirs_exist_ok=True)
    write(c.evidence/'continuation.json',json.dumps({
        'prior_run':'https://github.com/Self-Command/sp-sk-bridge-compat-ci/actions/runs/38253965707',
        'prior_report_unchanged':True,'prior_top_level_calls':4,'prior_reviewers':1,
        'git_history_note':'New runner imports byte-identical real product files. Original commit history is retained as prior-run logs; the imported snapshot is a new baseline commit.'},indent=2))
    return suite.finish()


if __name__=='__main__':
    raise SystemExit(main())
