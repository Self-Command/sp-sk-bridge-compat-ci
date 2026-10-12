"""One generated calculator project; real Codex tests every bridge entry."""
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time
import traceback

import yaml

from fixtures import create, write
from run_ci import Controller, InfrastructureError, MODEL
from sanitize import redact
from suite_verify import command_records, injected_skills, rows, tdd_order, preserved_contracts
from verify import digest, immutable_artifacts, tasks


CONTRACT='''Build calculator.py with add(a,b) for integers, returning their sum.
Only three unittest cases: add(2,3)==5, add(-2,2)==0, add(0,0)==0.
No CLI, UI, persistence, runtime dependencies, packaging or other behavior.
Use Python 3.13 and standard-library unittest. Run python -m unittest discover
-s tests -v. The scope and expected behavior are approved and unambiguous.
Prefer one cohesive implementation task; follow native SK templates where required.
Keep documents short. Only the model may generate design and implementation.
'''

SESSION='''# Approved compatibility session
Only gpt-6.1-sol; low reasoning for the main agent and every reviewer.
At most one reviewer per implementation call; no implementer subagents.
If review is required, spawn one fresh reviewer with model="gpt-6.1-sol",
reasoning_effort="low", fork_turns="none" and ask only for material findings.
All calculator requirements and branch finishing choice 3 (keep branch) are approved.
This is an isolated disposable feature checkout. Use the current directory.
Decline every optional extension hook; the answer is already given here.
Use standard-library unittest. No merge, push, publish, discard or new features.
Never modify installed skills, extension scripts, test harness or ci_hooks/.
Read required skills once and keep tool outputs and reports concise.
'''


HOOK_SCRIPT='''import json
from pathlib import Path
import subprocess
import sys

phase=sys.argv[1]
state=json.loads(Path('.specify/superpowers-handoff.json').read_text())
entry={'phase':phase,'feature':state.get('feature_directory'),
       'status_before':state.get('status'),'forced_failure':False}
code=0
if phase=='post':
    proc=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],capture_output=True,text=True)
    entry['suite_exit']=proc.returncode
    print(proc.stdout+proc.stderr)
    if proc.returncode: code=proc.returncode
    if Path('ci_hooks/FAIL_POST').exists():
        entry['forced_failure']=True
        code=23
elif phase=='skip':
    code=29
entry['exit_code']=code
with Path('.specify/ci-hook-events.jsonl').open('a') as out:
    out.write(json.dumps(entry)+'\\n')
print(json.dumps(entry))
raise SystemExit(code)
'''


class Suite:
    def __init__(self):
        self.c=Controller('latest-linux',call_limit=8,spawn_limit=2)
        self.required={'speckit-superpowers-bridge',
                       'speckit-speckit-superpowers-bridge-execute',
                       'speckit-speckit-superpowers-bridge-handoff',
                       'speckit-speckit-superpowers-bridge-guard'}

    def check(self,name,checks,**details):
        self.c.record(name,'pass' if all(checks.values()) else 'fail',json.dumps(checks),checks=checks,**details)
        return all(checks.values())

    def call(self,name,root,prompt,timeout=300):
        self.c.case_deadline=time.monotonic()+timeout+30
        result=self.c.call(name,root,prompt,'low',time_budget_seconds=timeout)
        self.check(name+' model process',{'exit_zero':result['exit_code']==0,
                                          'within_timeout':not result['termination_reason']})
        return result

    def setup(self):
        self.c.setup()
        config=self.c.home/'config.toml'
        config.write_text(config.read_text().replace('"xhigh"','"low"'),encoding='utf-8')
        reviewer=self.c.home/'agents/reviewer.toml'
        reviewer.write_text(reviewer.read_text().replace('"xhigh"','"low"'),encoding='utf-8')
        self.c.ready=True
        root=self.c.prepare('calculator-flow')
        write(root/'CI_CONSTRAINTS.md',SESSION)
        write(root/'APPROVED_REQUIREMENTS.md',CONTRACT)
        self.c.command('approved-inputs-add',['git','add','CI_CONSTRAINTS.md','APPROVED_REQUIREMENTS.md'],root)
        self.c.command('approved-inputs-commit',['git','commit','-m','test: approved tiny calculator scope'],root)
        self.root=root
        self.entry_hashes={str(p.relative_to(root)):digest(p) for p in (root/'.agents/skills').glob('*/SKILL.md')}

    def feature(self):
        pointer=json.loads((self.root/'.specify/feature.json').read_text(encoding='utf-8-sig'))
        value=pointer['feature_directory']
        return self.root/value

    def install_hooks(self):
        root=self.root
        write(root/'ci_hooks/record.py',HOOK_SCRIPT)
        for phase in ['pre','post','skip']:
            write(root/f'.agents/skills/speckit-ci-{phase}check/SKILL.md',f'''---
name: speckit-ci-{phase}check
description: Synthetic compatibility evidence hook for {phase} implementation.
---
Run `python ci_hooks/record.py {phase}` from repository root and wait for its
actual result. Do not change the script or any failure control file.
The post hook deliberately returns 23 when the operator sets FAIL_POST.
If it fails, stop and report its exit; do not claim completion or repair it.
''')
        registry=root/'.specify/extensions.yml'
        data=yaml.safe_load(registry.read_text(encoding='utf-8'))
        hooks=data.setdefault('hooks',{})
        pre={'extension':'ci-pre','command':'speckit.ci.precheck','optional':False,'condition':None,'description':'Record pre-implementation state'}
        post={'extension':'ci-post','command':'speckit.ci.postcheck','optional':False,'enabled':True,'condition':None,'description':'Verify tests and record post-implementation state'}
        skip={'extension':'ci-disabled','command':'speckit.ci.skipcheck','optional':False,'enabled':False,'condition':None,'description':'Disabled sentinel; must not execute'}
        conditional={**skip,'extension':'ci-conditional','enabled':True,'condition':'reserved-for-upstream'}
        optional={**skip,'extension':'ci-optional','enabled':True,'optional':True,'prompt':'Run the optional sentinel? Approved session answer is decline.'}
        hooks.setdefault('before_implement',[]).extend([pre,skip,conditional,optional])
        hooks.setdefault('after_implement',[]).append(post)
        write(registry,yaml.safe_dump(data,sort_keys=False))
        self.hook_hashes={str(p.relative_to(root)):digest(p) for p in (root/'ci_hooks').glob('*.py')}

    def design_first(self):
        self.call('01-design',self.root,'''Read APPROVED_REQUIREMENTS.md.
Use $speckit-constitution to establish binding requirements, Python standard
library/unittest, observed TDD, task commits, and keep branch. Then use
$speckit-specify for exactly the approved addition calculator feature;
use $speckit-clarify (no new requirements; no questions remain), then
$speckit-plan. Do not write application code or tasks yet. Native template
sections may be short; avoid unrelated setup, research, packaging and features.
''',360)
        feature=self.feature()
        paths=[self.root/'.specify/memory/constitution.md',feature/'spec.md',feature/'plan.md']
        valid=self.check('SK generated constitution specification and plan',{
            'all_generated':all(p.exists() and p.stat().st_size>100 for p in paths),
            'no_application_seeded':not (self.root/'calculator.py').exists()})
        if not valid: return False
        self.call('02-tasks-analysis',self.root,'''Use $speckit-tasks for this
small addition feature, with one cohesive code/test task where consistent with
native SK. Honor automatic mandatory hooks, including after_tasks handoff.
Then use $speckit-analyze read-only. Stop before implementation. No reviewers.
Do not manually create a handoff merely to mask a failed automatic hook.
''',240)
        feature=self.feature(); state=self.c.state(self.root)
        items=tasks(feature/'tasks.md') if (feature/'tasks.md').exists() else []
        events=rows(self.root/'.specify/bridge-events.jsonl')
        valid=self.check('SK tasks analyze and automatic handoff',{
            'tasks_generated':bool(items),'all_initially_pending':bool(items) and not any(t[1] for t in items),
            'automatic_handoff_ready':state.get('status')=='ready',
            'handoff_points_to_active_feature':state.get('feature_directory')==str(feature.relative_to(self.root)),
            'real_handoff_event':any(x.get('action')=='handoff' and x.get('status')=='ready' for x in events),
            'no_code_before_execution':not (self.root/'calculator.py').exists()})
        self.install_hooks()
        return valid

    def implementation_checks(self,name,before,result,operation,test_count,base):
        root=self.root;feature=self.feature();state=self.c.state(root)
        items=tasks(feature/'tasks.md')
        code=f'import calculator; assert calculator.{operation}(2,3)=={5 if operation=="add" else -1}; assert calculator.{operation}(-2,2)=={0 if operation=="add" else -4}; assert calculator.{operation}(0,0)==0; print("3 independent checks passed")'
        behavior=self.c.command(name+'-behavior',[sys.executable,'-c',code],root,check=False)
        suite=self.c.command(name+'-unittest',[sys.executable,'-m','unittest','discover','-s','tests','-v'],root,check=False)
        records=command_records(self.c.evidence/name/'events.jsonl')
        count=int(self.c.command(name+'-commits',['git','rev-list','--count',base+'..HEAD'],root).stdout.strip())
        branch=self.c.command(name+'-branch',['git','branch','--show-current'],root).stdout.strip()
        scratch=[]
        for p in (self.c.evidence/name/'scratch').glob('*.md'):
            text=p.read_text(encoding='utf-8')
            if re.search(r'^### Task \d+: T\d+',text,re.M):scratch.append(text)
        mapped=bool(scratch) and all(any(t[0] in s and t[2] in s for s in scratch) for t in items)
        flags=result['flags']
        checks={'external_behavior_pass':behavior.returncode==0,
                'expected_tests_pass':suite.returncode==0 and f'Ran {test_count} tests' in suite.stderr,
                'canonical_requirements_preserved':all(preserved_contracts(before,self.c.read_artifacts(root)).values()),
                'all_task_ids_checked':bool(items) and all(t[1] for t in items),
                'exact_task_adapter_observed':mapped,
                'real_TDD_failure_before_pass':tdd_order(records),
                'native_execution_and_verification':all(flags[k] for k in ['native_executor_read','tdd_read','verification_read']),
                'implementation_committed':count>=1,'feature_branch_kept':branch not in {'','main','master'},
                'original_hooks_unchanged':all(digest(root/p)==sha for p,sha in self.hook_hashes.items())}
        self.check(name+' product and SP discipline',checks,drift_warning=flags['drift_warning'])
        write(self.c.evidence/name/'external-checks.json',json.dumps(checks,indent=2))
        return state,all(checks.values())

    def execute_first(self):
        before=self.c.read_artifacts(self.root)
        base=self.c.command('first-execution-base',['git','rev-parse','HEAD'],self.root).stdout.strip()
        result=self.call('03-alias-execute',self.root,'''$speckit-superpowers-bridge
Execute this generated addition feature through the installed bridge alias and
native SP lifecycle, including actual extension hooks. Follow exact SK tasks;
do not redesign. Use one fresh low-reasoning gpt-6.1-sol reviewer, then keep branch.
No subtraction feature yet. Finish with complete only after mandatory post-hook.
''',300)
        state,product_ok=self.implementation_checks('03-alias-execute',before,result,'add',3,base)
        feature=state.get('feature_directory');hookrows=[x for x in rows(self.root/'.specify/ci-hook-events.jsonl') if x.get('feature')==feature]
        good=self.check('alias complete lifecycle and mandatory hook order',{
            'handoff_complete':state.get('status')=='complete',
            'real_reviewer_spawned':len(self.c.spawns)==1,
            'review_and_finish_skills_used':result['flags']['review_read'] and result['flags']['finish_read'],
            'pre_hook_before_executing':any(x['phase']=='pre' and x['status_before']=='ready' and x['exit_code']==0 for x in hookrows),
            'post_hook_before_complete':any(x['phase']=='post' and x['status_before']=='executing' and x['exit_code']==0 for x in hookrows),
            'disabled_conditional_optional_skipped':not any(x['phase']=='skip' for x in hookrows)})
        self.first_feature=feature
        self.first_code=(self.root/'calculator.py').read_text(encoding='utf-8') if (self.root/'calculator.py').exists() else ''
        return product_ok and good

    def second_feature(self):
        self.call('04-next-feature-design',self.root,'''The addition feature is complete.
Before creating the next feature, use the documented installed bridge auto-archive
script on the complete handoff. Then use $speckit-specify, $speckit-plan,
$speckit-tasks and $speckit-analyze, with mandatory hooks, for this approved
second tiny feature: append calculator.subtract(a,b), returning integer a-b.
Exactly three new unittest cases: subtract(2,3)==-1, subtract(-2,2)==-4,
subtract(0,0)==0. Preserve existing add and its three tests. No other feature.
Prefer one cohesive code/test task where native SK allows. Stop before code.
The user has approved this exact test-scope amendment as part of complete entry
coverage. If the constitution currently permits addition only, use the installed
$speckit-constitution skill to amend only that scope to allow the stated subtraction
and exactly three extra tests before planning; all prior principles still bind.
''',360)
        state=self.c.state(self.root);events=rows(self.root/'.specify/bridge-events.jsonl')
        feature=str(self.feature().relative_to(self.root))
        valid=self.check('completed feature archival and next feature handoff',{
            'new_feature_pointer':feature!=self.first_feature,
            'real_archive_event':any(x.get('action')=='archive' and x.get('feature_directory')==self.first_feature for x in events),
            'new_handoff_ready':state.get('status')=='ready' and state.get('feature_directory')==feature,
            'prior_code_preserved':(self.root/'calculator.py').read_text(encoding='utf-8')==self.first_code,
            'new_tasks_generated':(self.feature()/'tasks.md').exists() and bool(tasks(self.feature()/'tasks.md'))})
        return valid

    def fallback_and_recovery(self):
        before=self.c.read_artifacts(self.root)
        base=self.c.command('fallback-execution-base',['git','rev-parse','HEAD'],self.root).stdout.strip()
        write(self.root/'ci_hooks/FAIL_POST','Intentional external post-hook failure; only the controller may remove.\n')
        result=self.call('05-fallback-execute',self.root,'''$speckit-speckit-superpowers-bridge-execute
Use this installed canonical fallback entry to implement the subtraction feature
through native SP, exact canonical tasks, TDD, one low-reasoning gpt-6.1-sol
reviewer, verification and branch finishing. Mandatory hooks must really run.
This call tests an intentional post-hook exit 23: stop on the real failure,
keep handoff non-complete, report failure; do not repair the external hook.
''',300)
        state,product_ok=self.implementation_checks('05-fallback-execute',before,result,'subtract',6,base)
        feature=state.get('feature_directory');hookrows=[x for x in rows(self.root/'.specify/ci-hook-events.jsonl') if x.get('feature')==feature]
        failure_ok=self.check('fallback mandatory post-hook failure blocks completion',{
            'post_hook_really_failed_23':any(x['phase']=='post' and x.get('forced_failure') and x['exit_code']==23 for x in hookrows),
            'handoff_not_complete':state.get('status') in {'executing','blocked'},
            'failure_control_not_repaired':(self.root/'ci_hooks/FAIL_POST').exists()})
        if not (product_ok and failure_ok):
            self.c.record('fresh-session recovery','blocked','Prerequisite fallback execution or post-hook failure did not occur')
            return
        # Repair only the external fault fixture, never upstream skills or product.
        (self.root/'ci_hooks/FAIL_POST').unlink()
        code_before={str(p.relative_to(self.root)):digest(p) for p in [self.root/'calculator.py',*sorted((self.root/'tests').glob('*.py'))]}
        recovery=self.call('06-fresh-session-recovery',self.root,'''$speckit-superpowers-bridge
Fresh-session recovery of this same feature. The operator has removed only the
intentional external post-hook failure flag. Read real handoff and completed tasks;
resume the required post-hook, fresh verification and finishing. Do not repeat
completed tasks or rewrite code. Reuse the actual previous review if subtraction
code was reviewed; if the failing hook prevented review, use the one remaining
low-reasoning gpt-6.1-sol reviewer. Complete only after mandatory hook success,
required code review, fresh verification and branch finishing. Keep branch.
''',180)
        state=self.c.state(self.root);hookrows=[x for x in rows(self.root/'.specify/ci-hook-events.jsonl') if x.get('feature')==feature]
        failure_index=next((i for i,x in enumerate(hookrows) if x.get('forced_failure')),len(hookrows))
        later=hookrows[failure_index+1:]
        self.check('fresh-session recovery without repeating completed code',{
            'handoff_complete':state.get('status')=='complete',
            'all_tasks_still_checked':all(t[1] for t in tasks(self.feature()/'tasks.md')),
            'code_and_tests_unchanged':all(digest(self.root/p)==sha for p,sha in code_before.items()),
            'both_code_versions_reviewed':len(self.c.spawns)==2,
            'finishing_skill_used':recovery['flags']['finish_read'] or result['flags']['finish_read'],
            'mandatory_posthook_retried_successfully':any(x['phase']=='post' and x['exit_code']==0 and x.get('suite_exit')==0 for x in later)})

    def protocol_cases(self):
        root=self.c.prepare('protocol','smoke')
        write(root/'CI_CONSTRAINTS.md',SESSION+'\nProtocol-only call: no reviewer and no implementation.\n')
        missing=self.c.runtime/'projects/missing';conflict=self.c.runtime/'projects/conflict'
        for copy in [missing,conflict]:
            shutil.copytree(root,copy,ignore=shutil.ignore_patterns('.git','__pycache__'))
            self.c.command(copy.name+'-git-init',['git','init','-b','feature/'+copy.name],copy)
        (missing/'specs/001-smoke/plan.md').unlink()
        create(conflict,'conflict')
        before={str(p):self.c.read_artifacts(p) for p in [root,missing,conflict]}
        actions={'speckit.implement':'deny','superpowers:writing-plans':'deny',
                 'superpowers:brainstorming':'deny','speckit.constitution':'deny',
                 'speckit.tasks':'allow','superpowers:executing-plans':'allow',
                 'unrelated.action':'allow'}
        write(root/'PROTOCOL_CASES.md',f'''# Protocol fixtures
Do not implement, fix missing inputs, alter requirements or spawn reviewers.
1. Here, invoke installed handoff entry. Inspect actual handoff/schema/readiness.
   Transition to executing through selected native update-handoff script. Invoke
   installed guard entry for every action in this expected-decision dictionary:
   {json.dumps(actions)}. Actually run each guard command separately and obey it.
   Do not execute denied actions. Use bridge-status --readiness --json and normal
   bridge-status, and check they do not modify state/events. Mark blocked with
   reason "protocol fixture" through the documented script, then guard
   speckit.constitution again (expected allow). Verify original owner preserved.
2. In {missing}, invoke only installed handoff entry with missing plan.md.
   Preserve its FIRST script result even if it contradicts the skill document.
   Do not repair missing inputs or manually fix resulting state.
3. In {conflict}, invoke handoff, then the bridge alias. spec.md requires 42,
   plan/tasks require 99. Bridge must stop blocked with reason and no code.
   Return without repairing requirements or implementing either value.
''')
        result=self.call('07-protocol-entries',root,'''$speckit-speckit-superpowers-bridge-handoff
$speckit-speckit-superpowers-bridge-guard
$speckit-superpowers-bridge
Execute the protocol-only cases in PROTOCOL_CASES.md, in their listed directories.
Use installed entries and native selected scripts; report observed results briefly.
Expected deny/nonzero is test evidence, not permission to bypass a guard.
''',300)
        records=command_records(self.c.evidence/'07-protocol-entries/events.jsonl')
        events=rows(root/'.specify/bridge-events.jsonl')
        observed={}
        for x in events:
            if x.get('action')=='guard':observed.setdefault(x.get('checked_action'),[]).append(x.get('decision'))
        self.check('standalone guard all five rules and blocked repair permission',{
            **{action:decision in observed.get(action,[]) for action,decision in actions.items()},
            'constitution_allowed_after_block':'allow' in observed.get('speckit.constitution',[]),
            'canonical_docs_unchanged':all(immutable_artifacts(before[str(root)],self.c.read_artifacts(root)).values())})
        state=self.c.state(root)
        self.check('standalone handoff schema transitions and read-only readiness',{
            'handoff_required_fields':all(k in state for k in ['schema_version','feature_directory','source_of_truth','supersedes','executor','capabilities','status','artifact_owner']),
            'owner_preserved':state.get('artifact_owner')=='codex',
            'real_ready_executing_blocked':{'ready','executing','blocked'}<={x.get('status') for x in events if x.get('action')=='handoff'},
            'readiness_command_success':any('bridge-status' in x.get('command','') and '--readiness' in x['command'] and x.get('exit_code')==0 for x in records)})
        self.c.snapshot('07-missing-handoff',missing)
        state=self.c.state(missing)
        self.check('handoff missing artifact behavior matches its skill contract',{
            'missing_plan_unrepaired':not (missing/'specs/001-smoke/plan.md').exists(),
            'handoff_blocks_missing_plan':state.get('status')=='blocked',
            'canonical_docs_unchanged':all(immutable_artifacts(before[str(missing)],self.c.read_artifacts(missing)).values())},observed_state=state)
        self.c.snapshot('07-conflict-block',conflict)
        state=self.c.state(conflict)
        self.check('bridge stops requirements conflict without implementation',{
            'blocked_with_reason':state.get('status')=='blocked' and bool(state.get('blocked_reason')),
            'no_conflicting_product':not (conflict/'marker.py').exists(),
            'canonical_docs_unchanged':all(immutable_artifacts(before[str(conflict)],self.c.read_artifacts(conflict)).values())})

    def finish(self):
        self.c.finish()
        if hasattr(self,'entry_hashes'):
            self.check('installed upstream skills and bridge source remain original',{
                'generated_installed_skills_unchanged':all(digest(self.root/p)==sha for p,sha in self.entry_hashes.items()),
                'native_SP_skills_unchanged':all(digest(self.c.home/p)==sha for p,sha in self.c.plugin_files.items()),
                'bridge_release_files_unchanged':all(digest(self.root/'.specify/extensions/speckit-superpowers-bridge'/p)==sha
                    for p,sha in json.loads((self.c.evidence/'calculator-flow/installation.json').read_text())['bridge_file_hashes'].items())})
        loaded=injected_skills(self.c.evidence/'sessions')
        self.check('all four installed bridge skill entries consumed by real model',{
            name:name in loaded for name in sorted(self.required)},injected_skills=sorted(loaded))
        usage={'input_tokens':0,'cached_input_tokens':0,'output_tokens':0}
        for p in (self.c.evidence/'sessions').rglob('*.jsonl'):
            totals=[]
            for line in p.read_text(encoding='utf-8').splitlines():
                event=json.loads(line);payload=event.get('payload',{})
                info=payload.get('info') or {}
                if event.get('type')=='event_msg' and payload.get('type')=='token_count' and info.get('total_token_usage'):
                    totals.append(info['total_token_usage'])
            if totals:
                for k in usage:usage[k]+=totals[-1].get(k,0)
        write(self.c.evidence/'suite-usage.json',json.dumps(usage,indent=2))
        failures=[r['name'] for r in self.c.results if r['status']!='pass']
        text='\n'.join(['# Complete small-project bridge suite','',
            'Bridge 1.3.0 / Spec Kit 1.1.3 / Superpowers 7.0.0 / Codex 0.162.1 / Ubuntu 24.04.',
            f'Only {MODEL}, low reasoning. New controller calls {self.c.calls}/8; reviewers {len(self.c.spawns)}/2.',
            'One generated calculator project: addition alias, subtraction fallback, mandatory hook failure and fresh-session recovery.',
            'Protocol fixtures independently test handoff, all guard rules, missing inputs and conflict blocking.',
            '',*[f'- {r["name"]}: **{r["status"]}** — {r["detail"]}' for r in self.c.results],
            '',f'Session usage (includes reviewers): {json.dumps(usage)}.',
            'Results inspect tool commands and actual files; assistant success prose is never sufficient.',
            'Installed upstream files are unmodified. Other platforms and Claude Code are outside this run.',
            'Earlier run totals: 7 controller calls and 3 reviewers; prior evidence retained separately.',
            '',f'Overall: {"FAIL / incomplete coverage or incompatible behavior" if failures else "PASS"}.'])+'\n'
        write(self.c.evidence/'complete-report.md',text)
        if os.environ.get('GITHUB_STEP_SUMMARY'):
            with open(os.environ['GITHUB_STEP_SUMMARY'],'a',encoding='utf-8') as f:f.write(text)
        return 1 if failures else 0


def main():
    suite=Suite()
    try:
        suite.setup()
    except Exception as exc:
        write(suite.c.evidence/'suite-error.log',redact(traceback.format_exc()))
        suite.c.record('suite setup','blocked',str(exc))
        return suite.finish()
    try:
        if suite.design_first() and suite.execute_first():
            if suite.second_feature():suite.fallback_and_recovery()
            else:suite.c.record('fallback and recovery','blocked','Second generated feature prerequisites failed')
        else:suite.c.record('remaining project lifecycle','blocked','First generated feature prerequisites failed')
    except Exception as exc:
        write(suite.c.evidence/'suite-error.log',redact(traceback.format_exc()))
        suite.c.record('project lifecycle infrastructure or controller','blocked',str(exc))
    try:
        suite.protocol_cases()
    except Exception as exc:
        write(suite.c.evidence/'protocol-error.log',redact(traceback.format_exc()))
        suite.c.record('protocol scenarios infrastructure or controller','blocked',str(exc))
    return suite.finish()


if __name__=='__main__':
    raise SystemExit(main())
