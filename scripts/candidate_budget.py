"""Refuse a fresh paid rerun when this repair already has paid evidence.

Selective continuations must restore that evidence and its remaining budget;
this full-suite entry never silently resets the user's 20/6 allowance.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile


def gh(*args):
    return subprocess.check_output(['gh', *args], text=True, encoding='utf-8')


def main():
    repo=os.environ['GITHUB_REPOSITORY']
    current=int(os.environ['GITHUB_RUN_ID'])
    runs=json.loads(gh('api',f'repos/{repo}/actions/workflows/bridge-candidate.yml/runs?per_page=100'))['workflow_runs']
    ledger=[]
    with tempfile.TemporaryDirectory() as temporary:
        for run in runs:
            if run['id']==current:
                continue
            if run['status']!='completed':
                raise RuntimeError('Earlier candidate regression is unfinished; retain its budget before continuing')
            artifacts=json.loads(gh('api',f'repos/{repo}/actions/runs/{run["id"]}/artifacts'))['artifacts']
            for artifact in artifacts:
                if artifact['name'] not in {'candidate-full-linux','candidate-full-windows'}:
                    continue
                if artifact['expired']:
                    raise RuntimeError('Prior candidate evidence expired; paid budget cannot be established')
                target=Path(temporary)/str(run['id'])/artifact['name']
                gh('run','download',str(run['id']),'--repo',repo,'--name',artifact['name'],'--dir',str(target))
                found=list(target.rglob('results.json'))
                if len(found)!=1:
                    raise RuntimeError('Prior platform budget evidence is missing or ambiguous')
                data=json.loads(found[0].read_text())
                ledger.append({'run':run['id'],'lane':data['lane'],
                               'calls':data['model_calls'],'reviewers':data['reviewer_spawns']})
    output={'previous_calls':sum(row['calls'] for row in ledger),
            'previous_reviewers':sum(row['reviewers'] for row in ledger),
            'limits':{'calls':20,'reviewers':6},'previous_evidence':ledger}
    Path('candidate-budget.json').write_text(json.dumps(output,indent=2))
    print(json.dumps(output))
    if output['previous_calls'] or output['previous_reviewers']:
        raise RuntimeError('Paid evidence already exists. A selective continuation must reuse it; a full rerun would repeat passed work and reset the cumulative allowance')


if __name__=='__main__':
    main()
