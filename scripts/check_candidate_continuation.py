"""Free cumulative-budget gate for the one selective candidate continuation."""
import json
import os
from pathlib import Path
import subprocess

repo=os.environ['GITHUB_REPOSITORY']
current=int(os.environ['GITHUB_RUN_ID'])
assert os.environ.get('GITHUB_RUN_ATTEMPT','1')=='1','Rerun attempts must retain new paid evidence, never restart this continuation'
def api(path):
    return json.loads(subprocess.check_output(['gh','api',f'repos/{repo}/'+path],text=True))
for run in api('actions/workflows/continue-candidate.yml/runs?per_page=100')['workflow_runs']:
    if run['id']!=current:
        raise RuntimeError('Another selective continuation exists. Inspect its counters/evidence before further work; do not reset the cumulative allowance')
expected={'latest-linux':(9,2),'latest-windows':(2,1)}
indexes=[]
for lane,pair in expected.items():
    directory=Path('prior')/lane
    data=json.loads((directory/'results.json').read_text())
    assert (data['model_calls'],data['reviewer_spawns'])==pair
    versions=json.loads((directory/'versions.json').read_text())
    indexes.append(versions['candidate'])
assert indexes[0]==indexes[1]
assert indexes[0]['source_sha']=='048cf1e9b839ef34fcf1a36e0af2cabcc1d06e44'
data={'prior_calls':11,'prior_reviewers':3,'remaining_calls':9,'remaining_reviewers':3,
      'planned_additional':{'linux_calls':5,'windows_calls':4,'linux_reviewers':2,'windows_reviewers':1},
      'candidate':indexes[0]}
Path('continuation-budget.json').write_text(json.dumps(data,indent=2))
print(json.dumps(data))
