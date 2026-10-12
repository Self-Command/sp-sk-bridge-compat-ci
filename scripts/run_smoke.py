"""One small bridge project, one top-level model call, one short reviewer."""
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback
from run_ci import Controller, InfrastructureError
from sanitize import redact
from fixtures import write
from verify import immutable_artifacts, tasks


def main():
    controller=Controller('latest-linux',call_limit=1,spawn_limit=1)
    try:
        controller.setup()
        # Explicit smaller reasoning budgets for the tiny code and its reviewer.
        config=controller.home/'config.toml'
        config.write_text(config.read_text().replace('default_subagent_reasoning_effort = "xhigh"',
                                                   'default_subagent_reasoning_effort = "low"'))
        reviewer=controller.home/'agents/reviewer.toml'
        reviewer.write_text(reviewer.read_text().replace('"xhigh"','"low"'))
        root=controller.prepare('simple-bridge','smoke')
        constraints=root/'CI_CONSTRAINTS.md'
        constraints.write_text(constraints.read_text().replace('Use pytest for model-written tests.','Use standard-library unittest for model-written tests.'))
        before=controller.read_artifacts(root)
        base=controller.command('smoke-base',['git','rev-parse','HEAD'],root).stdout.strip()
        controller.case_deadline=__import__('time').monotonic()+360
        result=controller.call('simple-bridge-execute',root,
            '''This is a tiny bridge compatibility smoke test, not a new product design.
Use $speckit-speckit-superpowers-bridge-handoff on the existing fixed spec/plan/tasks,
then use $speckit-superpowers-bridge to execute its single canonical task through
native Superpowers. Do not regenerate any Spec Kit document, brainstorm or plan.
The only product is calculator.add(a,b), three unittest cases, no extra features.
Use at most one fresh reviewer, explicitly gpt-6.1-sol with low reasoning and
fork_turns="none"; ask it for only material findings in these two tiny files.
Read each required skill once, keep tool output concise. Finish by keeping branch.
Do not pause for approval; the exact feature and branch choice are preapproved.
''','low',time_budget_seconds=300)
        state=controller.state(root)
        canonical=tasks(root/'specs/001-smoke/tasks.md')
        command=[sys.executable,'-c','import calculator; assert calculator.add(2,3)==5; assert calculator.add(-2,2)==0; assert calculator.add(0,0)==0; print("3 external checks passed")']
        external=controller.command('external-calculator',command,root,check=False)
        suite=controller.command('external-unittest',[sys.executable,'-m','unittest','discover','-s','tests','-v'],root,check=False)
        branch=controller.command('smoke-branch',['git','branch','--show-current'],root).stdout.strip()
        count=int(controller.command('smoke-commits',['git','rev-list','--count',base+'..HEAD'],root).stdout.strip())
        flags=result['flags']
        checks={'real_handoff_and_bridge_script':flags['bridge_update'],
                'native_SP_executor_read':flags['native_executor_read'],
                'TDD_failure_then_pass':flags['red'] and flags['green'],
                'one_T001_checked':len(canonical)==1 and canonical[0][0]=='T001' and canonical[0][1],
                'three_external_behavior_checks':external.returncode==0,
                'generated_unit_suite_passes':suite.returncode==0 and 'Ran 3 tests' in suite.stderr,
                'canonical_requirements_preserved':all(immutable_artifacts(before,controller.read_artifacts(root)).values()),
                'handoff_complete':state.get('status')=='complete',
                'implementation_committed':count>=1,'feature_branch_kept':branch=='feature/simple-bridge'}
        scratch=list((controller.evidence/'simple-bridge-execute/scratch').glob('*.md'))
        adapter=[p for p in scratch if '### Task 1: T001' in p.read_text()]
        checks['exact_T001_adapter_observed']=any(canonical[0][2] in p.read_text() for p in adapter) if canonical else False
        write(controller.evidence/'simple-bridge-execute/external-checks.json',json.dumps(checks,indent=2))
        controller.record('simple bridge project','pass' if all(checks.values()) else 'fail',json.dumps(checks),checks=checks)
    except InfrastructureError as exc:
        controller.record('simple project infrastructure','blocked',str(exc))
    except Exception as exc:
        write(controller.evidence/'smoke-error.log',redact(traceback.format_exc()))
        controller.record('simple project controller','blocked',str(exc))
    finally:
        controller.finish()
        checks_path=controller.evidence/'results.json'
        rows=json.loads(checks_path.read_text())
        text='\n'.join(['# Simple bridge smoke test','',
            'Bridge 1.3.0 / Spec Kit 1.1.3 / Superpowers 7.0.0 / Codex 0.162.1.',
            f'Only gpt-6.1-sol; new top-level calls: {rows["model_calls"]}/1; reviewers: {rows["reviewer_spawns"]}/1.',
            '',*[f'- {r["name"]}: **{r["status"]}** — {r["detail"]}' for r in rows['scenarios']],
            '', 'Fixed one-task calculator fixture. No design generation, fault matrix or additional platforms.',
            'Earlier canceled runs are retained separately and are not a compatibility pass.'])+'\n'
        write(controller.evidence/'simple-report.md',text)
        if os.environ.get('GITHUB_STEP_SUMMARY'):
            with open(os.environ['GITHUB_STEP_SUMMARY'],'a',encoding='utf-8') as stream:
                stream.write(text)


if __name__=='__main__':
    main()
