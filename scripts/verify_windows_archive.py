"""Finish Windows archival verification from its actual product: zero model calls."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import urllib.request
import zipfile

from fixtures import write
from full_verify import contract_ok, product, run, tests_pass
from run_ci import ROOT
from suite_verify import rows
from verify import digest


def documents(root):
    return {str(p.relative_to(root)):p.read_text(encoding='utf-8-sig') for p in
            [root/'.specify/memory/constitution.md',*sorted((root/'specs').glob('*/*.md'))] if p.exists()}


def main():
    prior=Path(os.environ['PRIOR_EVIDENCE'])/'latest-windows'
    snapshot=prior/'04-windows-main-execute/snapshot'
    initial=prior/'03-sk-tasks-checklist-analyze/snapshot'
    evidence=ROOT/'evidence/latest-windows'
    evidence.mkdir(parents=True,exist_ok=True)
    root=ROOT/'.runtime/native-windows-archive'
    shutil.copytree(snapshot,root)
    lock=json.loads((ROOT/'versions-lock.json').read_text())
    archive=root.parent/'original-bridge-v1.3.0.zip'
    urllib.request.urlretrieve(lock['bridge']['asset'],archive)
    if digest(archive)!=lock['bridge']['asset_sha256']:raise RuntimeError('Published ZIP hash mismatch')
    extension=root/'.specify/extensions/speckit-superpowers-bridge'
    original={}
    with zipfile.ZipFile(archive) as z:
        prefix=next(p for p in z.namelist() if p.endswith('extension.yml'))[:-len('extension.yml')]
        for entry in z.namelist():
            if entry.endswith('/') or not entry.startswith(prefix):continue
            rel=entry[len(prefix):];target=extension/rel
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(entry))
            original[rel]=digest(target)
    for args in [['git','init','-b','main'],['git','config','user.name','Compatibility Fixture'],
                 ['git','config','user.email','fixture@example.invalid']]:
        subprocess.run(args,cwd=root,capture_output=True,check=True)
    canonical=contract_ok(documents(initial),documents(root))
    behavior=product(root);test=run(root,['-m','unittest','discover','-s','tests','-v'])
    state=json.loads((root/'.specify/superpowers-handoff.json').read_text(encoding='utf-8-sig'))
    if not canonical or not behavior['pass'] or not tests_pass(test) or state['status']!='complete':
        raise RuntimeError('Actual Windows product prerequisites failed; do not fabricate completion')
    before={str(p.relative_to(root)):digest(p) for p in [root/'resume_app.py',*sorted((root/'tests').glob('*.py'))]}
    ps=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
    command=[str(ps),'-NoProfile','-ExecutionPolicy','Bypass','-File',str(extension/'scripts/powershell/auto-archive-handoff.ps1'),'-Actor','codex']
    p=subprocess.run(command,cwd=root,capture_output=True,text=True,encoding='utf-8',errors='replace')
    after=json.loads((root/'.specify/superpowers-handoff.json').read_text(encoding='utf-8-sig'))
    events=rows(root/'.specify/bridge-events.jsonl')
    checks={'native_exit_zero':p.returncode==0,'real_archive_event':any(x.get('action')=='archive' for x in events),
            'ready_with_pointer_cleared':after['status']=='ready' and after.get('feature_directory') is None,
            'product_tests_unchanged':all(digest(root/rel)==sha for rel,sha in before.items()),
            'original_release_unchanged':all(digest(extension/rel)==sha for rel,sha in original.items())}
    if not all(checks.values()):raise RuntimeError('Native Windows archival check failed: '+json.dumps(checks))
    previous=json.loads((prior/'results.json').read_text(encoding='utf-8'))
    for row in previous['scenarios']:
        if row['name']=='main product external acceptance and task completion':
            row['checks']['canonical_contract_preserved']=canonical
            row['status']='pass' if all(row['checks'].values()) else 'fail'
            row['detail']=json.dumps(row['checks'])
            row['external_recheck']='Only checkbox changes and append-only task/final-review evidence; original requirements and IDs unchanged.'
        if row['name']=='completed handoff archival':
            row.update(status='pass',checks=checks,detail=json.dumps(checks),external_recheck='Actual Windows model-completed consumer; fresh original PowerShell 5.1 script, no new model call.')
    write(evidence/'reviewed-results.json',json.dumps(previous,ensure_ascii=False,indent=2))
    write(evidence/'archive-independent-checks.json',json.dumps({'checks':checks,'behavior':behavior,'tests':test,
          'command':command,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'source_run':'38271885332',
          'new_model_calls':0,'new_reviewers':0,'original_release_hashes':original},ensure_ascii=False,indent=2))
    write(evidence/'archive-handoff.json',json.dumps(after,indent=2))
    shutil.copyfile(root/'.specify/bridge-events.jsonl',evidence/'archive-bridge-events.jsonl')
    print(json.dumps({'new_model_calls':0,'new_reviewers':0,'checks':checks},ensure_ascii=False))


if __name__=='__main__':main()
