"""Independent free inspection of retained counters and convergence snapshots."""
import json
from pathlib import Path
import sys

from fixtures import write
from full_verify import model_metadata
from run_candidate_suite import CONVERGE_SCENARIOS
from run_full_suite import COMMON_EXPECTED,LINUX_EXPECTED


def inspect(root):
    root=Path(root)
    checks={};indexes=[];totals={'calls':0,'reviewers':0}
    for lane in ('latest-linux','latest-windows'):
        directory=root/lane
        results=json.loads((directory/'results.json').read_text())
        actual={row['name']:row['status'] for row in results['scenarios']}
        expected=COMMON_EXPECTED+CONVERGE_SCENARIOS+([] if lane.endswith('windows') else LINUX_EXPECTED)
        checks[lane+'/required_coverage']=all(actual.get(name)=='pass' for name in expected)
        invocations=list(directory.glob('*/invocation.json'))
        checks[lane+'/actual_main_invocation_count']=len(invocations)==results['model_calls']
        for invocation in invocations:
            data=json.loads(invocation.read_text())
            checks[lane+'/'+invocation.parent.name+'/fixed_model']=data['model']=='gpt-6.1-sol' and data['reasoning']=='low'
        metadata=model_metadata(directory/'sessions')
        checks[lane+'/actual_reviewer_count']=len(metadata['spawns'])==results['reviewer_spawns']
        totals['calls']+=results['model_calls'];totals['reviewers']+=results['reviewer_spawns']
        index=json.loads((directory/'candidate-coverage.json').read_text())['source']
        indexes.append(index)
        main=directory/('04-windows-main-execute' if lane.endswith('windows') else '14-completed-product')/'snapshot'
        feature=json.loads((main/'.specify/feature.json').read_text())['feature_directory']
        product_paths=[p.relative_to(main) for p in main.rglob('*.py')
                       if p.name=='resume_app.py' or p.name.startswith('test_')]
        checks[lane+'/real_product_and_tests_present']=any(p.name=='resume_app.py' for p in product_paths) and any(p.name.startswith('test_') for p in product_paths)
        for kind in ('clean','gap','post-failure','ineligible'):
            case=directory/('11-convergence-'+kind)/'snapshot'
            for relative in product_paths:
                original=(main/relative).read_bytes()
                if kind=='gap' and relative.name=='resume_app.py':
                    original+=b'\n# Deliberate external convergence assessment fault\nmake_task = lambda title: {"title": normalize_title(title), "completed": True}\n'
                checks[lane+'/'+kind+'/'+relative.as_posix()+'/unchanged']=((case/relative).read_bytes()==original)
            for name in ('spec.md','plan.md'):
                checks[lane+'/'+kind+'/'+name+'/unchanged']=(case/feature/name).read_bytes()==(main/feature/name).read_bytes()
            native=Path('.agents/skills/speckit-converge/SKILL.md')
            checks[lane+'/'+kind+'/native_SK_unchanged']=(case/native).read_bytes()==(main/native).read_bytes()
            before=(main/feature/'tasks.md').read_bytes();after=(case/feature/'tasks.md').read_bytes()
            checks[lane+'/'+kind+'/tasks_contract']=after.startswith(before) and len(after)>len(before) if kind=='gap' else after==before
    checks['both_platforms_same_candidate']=len(indexes)==2 and indexes[0]==indexes[1]
    checks['cumulative_20_6']=totals['calls']<=20 and totals['reviewers']<=6
    output={'passed':all(checks.values()),'checks':checks,'actual_totals':totals,'candidate':indexes[0]}
    write(root/'independent-candidate-evidence.json',json.dumps(output,indent=2))
    print(json.dumps({'passed':output['passed'],'totals':totals,'failed':[key for key,value in checks.items() if not value]}))
    return 0 if output['passed'] else 1


if __name__=='__main__':raise SystemExit(inspect(sys.argv[1]))
