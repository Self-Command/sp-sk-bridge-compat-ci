"""Original-release full suite: 14/6 controller calls and 4/2 reviewers at most.

The controller supplies approved answers and deliberate faults, never product
solutions. Models use installed skills; all grading happens outside consumers.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import time
import traceback
import urllib.request
import zipfile

import yaml

from fixtures import write, create
from full_verify import (CONTRACT, ast_function, contract_ok, model_metadata, product,
                         protected_hashes, protected_ok, records, run, skill_read,
                         task_adapter_check, tests_pass, usage, yaml_problem_reported)
from full_verify import test_suite
from run_ci import Controller, InfrastructureError, ROOT, WIN
from sanitize import redact
from suite_verify import injected_skills, rows, tdd_order
from verify import digest, tasks


SESSION='''# Authorized full compatibility test
Only gpt-6.1-sol and low reasoning for main agent and every reviewer. Read this
file first. At most the explicitly stated number of review agents; no implementer
agents. Specify model="gpt-6.1-sol", reasoning_effort="low", fork_turns="none".
The entire fixed title-task scope in APPROVED_INPUTS.md and scripted testing
answers are approved. This is an isolated disposable checkout. Use this checkout
unless BRANCH_CASES.md explicitly authorizes creating its test worktrees.
Use standard-library unittest and observed red/green tests. No new features.
Only SK produces canonical spec/plan/tasks; only model executes product work.
Never modify installed skills, bridge release files, ci_hooks scripts, or the
external controller/verifier. Do not print credentials or inspect auth files.
Optional hooks: accept ci-accepted, decline ci-declined. Nonempty conditions
belong to upstream and must be skipped. Fault flags are external controls:
never remove or rewrite them. Mandatory hook failure stops completion.
Keep the feature branch by default. Only BRANCH_CASES.md may authorize a local
merge or push/PR into its specifically named test branches; never merge to main.
Read required skills once, keep outputs concise and use actual tool evidence.
'''

HOOK_SCRIPT='''import json,re,subprocess,sys
from pathlib import Path
phase=sys.argv[1]
p=Path('.specify/superpowers-handoff.json')
s=json.loads(p.read_text(encoding='utf-8-sig')) if p.exists() else {}
code=0
entry={'phase':phase,'status_before':s.get('status'),'feature':s.get('feature_directory')}
if phase=='pre' and Path('ci_hooks/FAIL_PRE').exists():code=17
if phase=='post':
 args=[sys.executable,'-m','unittest','discover']
 if Path('tests').is_dir():args+=['-s','tests']
 p=subprocess.run([*args,'-v'],capture_output=True,text=True)
 print(p.stdout+p.stderr)
 entry['suite_exit']=p.returncode
 code=p.returncode
 if code==0 and not re.search(r'Ran [1-9]\\d* tests?\\b[\\s\\S]*\\bOK\\b',p.stdout+p.stderr):code=6
 if Path('ci_hooks/FAIL_POST').exists():code=23
if phase=='sentinel':code=29
entry['exit_code']=code
with Path('.specify/full-hook-events.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(entry)+'\\n')
print(json.dumps(entry))
raise SystemExit(code)
'''

COMMON_EXPECTED=['SP brainstorming produces PRD with real builder check',
                 'SK generates approved constitution spec and plan',
                 'SK three tasks checklist analysis and automatic handoff',
                 'main product external acceptance and task completion',
                 'native TDD review verification and keep-branch evidence',
                 'four bridge entries actual model use',
                 'guard rules and schema transitions',
                 'missing spec handoff blocks', 'missing plan handoff blocks',
                 'missing tasks handoff blocks', 'requirements conflict blocks',
                 'status and readiness are read-only', 'completed handoff archival',
                 'original installed skills and release scripts unchanged',
                 'only approved model reasoning and call budgets']
LINUX_EXPECTED=['mandatory pre-hook failure prevents implementation',
                'committed first task interruption', 'canonical resume adapter identity',
                'systematic debugging repairs injected completed-task fault',
                'mandatory post-hook failure prevents completion',
                'fresh-session post-hook recovery does not rewrite product',
                'review finds candidate defect and remediation re-review passes',
                'accepted declined disabled conditional hooks',
                'missing hook registry lifecycle', 'malformed hook registry lifecycle',
                'converge after SP implementation compatibility',
                'taskstoissues real MCP creation and deduplication',
                'native worktree local merge and cleanup',
                'native PR creation against test base']


class FullSuite:
    def __init__(self,lane):
        self.lane=lane
        self.c=Controller(lane,call_limit=6 if WIN else 14,spawn_limit=2 if WIN else 4)
        self.expected=COMMON_EXPECTED+([] if WIN else LINUX_EXPECTED)
        self.completed_root=None
        self.native_hashes={}
        self.protected={}
        self.case_number=0

    def record(self,name,checks=None,status=None,detail='',**extra):
        if checks is not None:
            status='pass' if all(checks.values()) else 'fail'
            extra['checks']=checks
            detail=json.dumps(checks,ensure_ascii=False)
        self.c.record(name,status or 'blocked',detail,**extra)
        print(f'{self.lane}: {name}: {status}',flush=True)
        return status=='pass'

    def call(self,name,root,prompt,timeout=300,reviewers=0,**kw):
        self.c.case_deadline=time.monotonic()+timeout+30
        prior=len(self.c.spawns)
        p=self.c.call(name,root,prompt,'low',time_budget_seconds=timeout,
                      max_reviewers=reviewers,**kw)
        if len(self.c.spawns)-prior>reviewers:
            raise InfrastructureError('Per-call review budget exceeded: '+name)
        self.record(name+' process',{'exit_zero':p['exit_code']==0,
                                   'within_timeout':not p['termination_reason']}
                    if not p['interrupted'] else {'intentional_interrupt':True},process=p)
        return p

    def safe_stage(self,name,fn):
        try:return fn()
        except InfrastructureError:
            raise
        except Exception as exc:
            write(self.c.evidence/(name+'-error.log'),redact(traceback.format_exc()))
            self.record(name,status='blocked',detail=f'Test infrastructure: {type(exc).__name__}: {exc}')
            return False

    def setup(self):
        self.c.setup()
        for p in [self.c.home/'config.toml',self.c.home/'agents/reviewer.toml']:
            write(p,p.read_text().replace('"xhigh"','"low"'))
        for p in (self.c.home/'plugins').rglob('SKILL.md'):
            self.native_hashes[str(p.relative_to(self.c.home))]=digest(p)
        self.root=self.c.prepare('title-task-full')
        self.protected[self.root]=protected_hashes(self.root)
        self.c.ready=True
        self.inputs(self.root)
        self.c.command('full-inputs-add',['git','add','CI_CONSTRAINTS.md','APPROVED_INPUTS.md'],self.root)
        self.c.command('full-inputs-commit',['git','commit','-m','test: approved full-suite title-task scope'],self.root)
        self.record('fixed originals installed',{'bridge_130':True,'SK_113':True,'SP_700':True,'codex_01621':True})

    def inputs(self,root):
        write(root/'CI_CONSTRAINTS.md',SESSION)
        write(root/'APPROVED_INPUTS.md',CONTRACT)

    def feature(self,root=None):
        root=root or self.root
        return root/json.loads((root/'.specify/feature.json').read_text(encoding='utf-8-sig'))['feature_directory']

    def clone(self,name,source=None):
        source=source or self.root
        target=self.c.runtime/'projects'/name
        shutil.copytree(source,target,ignore=shutil.ignore_patterns('.git','__pycache__','.superpowers','.worktrees'))
        self.inputs(target)
        self.c.command(name+'-init',['git','init','-b','main'],target)
        self.c.command(name+'-name',['git','config','user.name','Compatibility Fixture'],target)
        self.c.command(name+'-email',['git','config','user.email','fixture@example.invalid'],target)
        self.c.command(name+'-add',['git','add','.'],target)
        self.c.command(name+'-commit',['git','commit','-m','test: isolated full-suite snapshot'],target)
        self.c.command(name+'-branch',['git','switch','-c','feature/'+name],target)
        self.protected[target]=protected_hashes(target)
        return target

    def shell(self,stem,*args):
        extension='.ps1' if WIN else '.sh'
        folder='powershell' if WIN else 'bash'
        script='.specify/extensions/speckit-superpowers-bridge/scripts/'+folder+'/'+stem+extension
        if WIN:
            powershell=str(Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe')
            converted=[]
            mapping={'--status':'-Status','--actor':'-Actor','--reason':'-Reason',
                     '--action':'-Action','--readiness':'-Readiness','--json':'-Json'}
            for a in args:converted.append(mapping.get(a,a))
            return [powershell,'-NoProfile','-ExecutionPolicy','Bypass','-File',script,*converted]
        return ['bash',script,*args]

    def hooks(self,root):
        write(root/'ci_hooks/record.py',HOOK_SCRIPT)
        for phase in ['pre','post','accepted','declined','sentinel']:
            write(root/f'.agents/skills/speckit-ci-{phase}/SKILL.md',f'''---
name: speckit-ci-{phase}
description: Full compatibility fixture {phase} hook.
---
Run `python ci_hooks/record.py {phase}` from repository root and wait for its result.
Never change the script or remove external fault flags. Report a failure and stop.
''')
        registry=root/'.specify/extensions.yml'
        d=yaml.safe_load(registry.read_text(encoding='utf-8-sig'))
        def hook(phase,**kw):
            return {'extension':'ci-'+phase,'command':'speckit.ci.'+phase,
                    'optional':False,'enabled':True,'condition':None,
                    'description':'Synthetic full-test '+phase,**kw}
        d.setdefault('hooks',{}).setdefault('before_implement',[]).extend([
            hook('pre'),hook('accepted',optional=True,prompt='Approved test answer: accept.'),
            hook('declined',optional=True,prompt='Approved test answer: decline.'),
            hook('disabled',command='speckit.ci.sentinel',enabled=False),
            hook('conditional',command='speckit.ci.sentinel',condition='reserved-for-upstream')])
        d['hooks'].setdefault('after_implement',[]).append(hook('post'))
        write(registry,yaml.safe_dump(d,sort_keys=False))

    def design(self):
        count=len(self.c.spawns)
        self.call('01-brainstorm-prd',self.root,'''Use installed native Superpowers
brainstorming, reading its original SKILL.md and builder-check instructions.
Read APPROVED_INPUTS.md. The user approved a fixed tiny compatibility fixture:
its target user automates creation of a task JSON from a title; success is every
documented library/CLI behavior. All ground-covering answers are in that input.
No product questions remain. Write concise docs/product/title-task-prd.md with
intent, user story, boundaries, error/Unicode cases and acceptance criteria.
Dispatch exactly one fresh low-reasoning gpt-6.1-sol reviewer using native
brainstorming's builder-check prompt. Address material findings within scope.
The user explicitly overrides brainstorming's default writing-plans handoff:
STOP after the PRD and builder check. Formal spec/plan/tasks belong to SK next.
Do not write application code, scaffolding or tests. Do not invoke writing-plans.
''',360,reviewers=1)
        p=self.root/'docs/product/title-task-prd.md'
        text=p.read_text(encoding='utf-8') if p.exists() else ''
        good=self.record('SP brainstorming produces PRD with real builder check',{
            'prd_written':len(text)>150,
            'approved_interfaces_present':all(k in text for k in ['normalize_title','make_task','resume_app.py']),
            'builder_review_spawned':len(self.c.spawns)-count==1,
            'native_brainstorming_read':skill_read(records(self.c.evidence,'01-brainstorm-prd'),'brainstorming',
                (self.c.sources['superpowers']/'skills/brainstorming/SKILL.md').read_text()),
            'no_application_before_SK':not (self.root/'resume_app.py').exists()})
        if not good:return False
        self.call('02-sk-design',self.root,'''Use $speckit-constitution,
$speckit-specify, $speckit-clarify, then $speckit-plan. Read APPROVED_INPUTS.md
and docs/product/title-task-prd.md as the approved pre-spec input. Preserve all
interfaces, Unicode/empty rules, exact JSON and exit codes. No unanswered
product questions. Constitution: standard-library unittest, observed TDD,
three dependent tasks, per-task commit, keep branch, canonical SK ownership.
Write native short spec/plan and other required design artifacts. Cite the PRD.
Do not implement or generate tasks yet. Honor installed mandatory guard hooks.
''',360)
        feature=self.feature()
        good=self.record('SK generates approved constitution spec and plan',{
            'all_documents':all(p.exists() and p.stat().st_size>100 for p in [
                self.root/'.specify/memory/constitution.md',feature/'spec.md',feature/'plan.md']),
            'no_product_yet':not (self.root/'resume_app.py').exists()})
        if not good:return False
        self.call('03-sk-tasks-checklist-analyze',self.root,'''Use $speckit-tasks,
$speckit-checklist, and $speckit-analyze in that order. Honor after_tasks
automatic handoff; do not manually mask a failed automatic hook. The approved
implementation breakdown is exactly T001 normalize_title plus tests, T002
make_task plus tests depending on T001, T003 CLI plus tests depending on both.
No separate packaging, directory scaffolding or polish tasks are needed for
this one-module standard-library fixture. Each task must require observed
red/green tests, checkbox/evidence recording and commit. Checklist checks
requirements quality, including explicit Unicode, empty-title and exit rules.
Each task must explicitly require append-only execution evidence in its
canonical tasks.md under a `## T### execution evidence` heading.
Keep the native document formats, avoid extra requirements, stop before code.
''',360)
        feature=self.feature();items=tasks(feature/'tasks.md');s=self.c.state(self.root)
        good=self.record('SK three tasks checklist analysis and automatic handoff',{
            'three_pending_ids':[(t[0],t[1]) for t in items]==[('T001',False),('T002',False),('T003',False)],
            'automatic_ready':s.get('status')=='ready',
            'automatic_event':any(e.get('action')=='handoff' and e.get('status')=='ready'
                                  for e in rows(self.root/'.specify/bridge-events.jsonl')),
            'checklist_artifact':any(p.stat().st_size>80 for p in (feature/'checklists').glob('*.md')),
            'no_application_before_bridge':not (self.root/'resume_app.py').exists()})
        if good:
            self.original_artifacts=self.c.read_artifacts(self.root)
            self.original_tasks=(feature/'tasks.md').read_text(encoding='utf-8')
            self.hooks(self.root)
            self.main_tasks_base=self.c.command('main-base',['git','rev-parse','HEAD'],self.root).stdout.strip()
        return good

    def execute(self):
        if WIN:
            count=len(self.c.spawns)
            self.call('04-windows-main-execute',self.root,'''$speckit-superpowers-bridge
Execute all three canonical tasks using native SP executing-plans and TDD.
Honor real hooks and exact canonical IDs; record observed tests and per-task
commits. Use one fresh low-reasoning gpt-6.1-sol code reviewer. Verify, finish
by keeping the branch and complete only after the mandatory post-hook passes.
''',600,reviewers=1)
            self.main_call_names=['04-windows-main-execute']
            self.record('Windows actual final reviewer',{'one_fresh_reviewer':len(self.c.spawns)-count==1})
            return self.main_acceptance()
        write(self.root/'ci_hooks/FAIL_PRE','External intentional pre-hook exit 17.\n')
        self.call('04-pre-hook-failure',self.root,'''$speckit-superpowers-bridge
Start the installed bridge normally. The mandatory pre-hook deliberately exits
17. Stop on its actual failure, leave the handoff non-executing and no product.
Never remove the flag or bypass the hook; no reviewer or implementation.
''',180)
        s=self.c.state(self.root)
        self.record('mandatory pre-hook failure prevents implementation',{
            'actual_exit17':any(e.get('phase')=='pre' and e.get('exit_code')==17
                               for e in rows(self.root/'.specify/full-hook-events.jsonl')),
            'not_executing':s.get('status')!='executing',
            'no_product':not (self.root/'resume_app.py').exists(),
            'external_flag_preserved':(self.root/'ci_hooks/FAIL_PRE').exists()})
        (self.root/'ci_hooks/FAIL_PRE').unlink(missing_ok=True)
        feature=self.feature();rel=str((feature/'tasks.md').relative_to(self.root)).replace('\\','/')
        def committed_first():
            if not (feature/'tasks.md').exists() or not any(t[0]=='T001' and t[1] for t in tasks(feature/'tasks.md')):
                return False
            p=self.c.command('interrupt-commit-check',['git','show','HEAD:'+rel],self.root,check=False)
            ledgers=list((self.root/'.superpowers').rglob('progress.md'))
            native_done=any(re.search(r'^Task 1: complete\b',f.read_text(encoding='utf-8'),re.M) for f in ledgers)
            return p.returncode==0 and '- [x] T001' in p.stdout and not '- [x] T003' in p.stdout and native_done
        interrupted=self.call('05-interrupt-after-task1',self.root,'''$speckit-superpowers-bridge
Execute the three canonical tasks with native SP and TDD, exact temporary
adapter mappings and per-task commits containing code/tests/checkbox evidence.
No reviewer in this invocation: an external controller will interrupt after
the first committed task. Keep native progress; do not batch all tasks into
one implementation/commit. Check canonical tasks before each next task.
''',420,interrupt_check=committed_first)
        items=tasks(feature/'tasks.md')
        ok=self.record('committed first task interruption',{
            'externally_interrupted':interrupted['interrupted'],
            'first_done_remaining_pending':[(t[0],t[1]) for t in items]==[('T001',True),('T002',False),('T003',False)],
            'first_function_exists':(self.root/'resume_app.py').exists() and ast_function(self.root/'resume_app.py','normalize_title') is not None})
        if not ok:return False
        self.first_function=ast_function(self.root/'resume_app.py','normalize_title')
        original=(self.root/'resume_app.py').read_text(encoding='utf-8')
        write(self.root/'resume_app.py',original+'\n# Deliberate external compatibility fault\nnormalize_title = lambda title: title\n')
        write(self.c.evidence/'injected-debug-fault.json',json.dumps({'kind':'completed T001 function rebound without strip/validation',
              'original_sha256':hashlib.sha256(original.encode()).hexdigest(),'injected_sha256':digest(self.root/'resume_app.py')},indent=2))
        write(self.root/'ci_hooks/FAIL_POST','External intentional post-hook exit 23.\n')
        count=len(self.c.spawns)
        self.call('06-resume-debug-post-failure',self.root,'''$speckit-speckit-superpowers-bridge-execute
Fresh session after external interruption of committed T001. T002 and T003
remain pending. The controller deliberately corrupted completed T001 by
appending a normalize_title rebinding. First observe the real failure and use
native SP systematic-debugging before repairing this injected product fault.
Preserve T001's canonical identity and completion; do not reimplement its task.
Resume the remaining IDs through exact native adapters, TDD and commits.
Use exactly one fresh low-reasoning gpt-6.1-sol final code reviewer, fresh
verification and keep-branch finishing. The mandatory post-hook is externally
set to exit 23: invoke it, stop on failure, keep a non-complete handoff. Do not
remove that flag or invent a successful hook result.
''',600,reviewers=1)
        self.main_call_names=['05-interrupt-after-task1','06-resume-debug-post-failure']
        rec=records(self.c.evidence,'06-resume-debug-post-failure')
        remaining=['T002','T003']
        adapter,detail=task_adapter_check(self.c.evidence/'06-resume-debug-post-failure',self.original_tasks,remaining)
        self.record('canonical resume adapter identity',{'remaining_ids_mapped_exactly':adapter},mapping=detail)
        library=run(self.root,['-c',"import resume_app as a; assert a.normalize_title(' X ')=='X';\ntry: a.normalize_title(' ')\nexcept ValueError: pass\nelse: raise AssertionError('empty accepted')"])
        self.record('systematic debugging repairs injected completed-task fault',{
            'native_debugging_used':skill_read(rec,'systematic-debugging'),
            'actual_failed_then_passed_tests':tdd_order(rec),
            'repaired_behavior':library['exit_code']==0})
        self.record('mandatory post-hook failure prevents completion',{
            'actual_exit23':any(e.get('phase')=='post' and e.get('exit_code')==23
                               for e in rows(self.root/'.specify/full-hook-events.jsonl')),
            'not_complete':self.c.state(self.root).get('status') in {'executing','blocked'},
            'reviewer_was_real':len(self.c.spawns)-count==1,
            'flag_preserved':(self.root/'ci_hooks/FAIL_POST').exists()})
        if not product(self.root)['pass'] or not all(t[1] for t in tasks(feature/'tasks.md')):
            return False
        (self.root/'ci_hooks/FAIL_POST').unlink(missing_ok=True)
        before={str(p.relative_to(self.root)):digest(p) for p in [self.root/'resume_app.py',*sorted((self.root/'tests').glob('*.py'))]}
        count=len(self.c.spawns)
        self.call('07-post-hook-recovery',self.root,'''$speckit-superpowers-bridge
Fresh-session recovery. All canonical tasks are actually complete and the last
code version has an actual independent review. The controller removed only the
external FAIL_POST flag. Reuse that real review, rerun required post-hook and
fresh verification/finishing. No reviewer, no repeated tasks, no code rewrite.
Only transition to complete after real post-hook success and passing tests.
''',240)
        self.main_call_names.append('07-post-hook-recovery')
        self.record('fresh-session post-hook recovery does not rewrite product',{
            'complete':self.c.state(self.root).get('status')=='complete',
            'code_tests_unchanged':all(digest(self.root/p)==sha for p,sha in before.items()),
            'no_new_reviewer':len(self.c.spawns)==count,
            'actual_successful_post':any(e.get('phase')=='post' and e.get('exit_code')==0
                                        for e in rows(self.root/'.specify/full-hook-events.jsonl'))})
        return self.main_acceptance()

    def main_acceptance(self):
        acceptance=product(self.root);test=test_suite(self.root)
        write(self.c.evidence/'main-external-acceptance.json',json.dumps({'behavior':acceptance,'tests':test},ensure_ascii=False,indent=2))
        good=self.record('main product external acceptance and task completion',{
            'external_behavior':acceptance['pass'],'real_nonempty_suite':tests_pass(test),
            'all_three_done':[(t[0],t[1]) for t in tasks(self.feature()/'tasks.md')]==[('T001',True),('T002',True),('T003',True)],
            'complete':self.c.state(self.root).get('status')=='complete',
            'canonical_contract_preserved':contract_ok(self.original_artifacts,self.c.read_artifacts(self.root))})
        rec=[]
        for name in self.main_call_names:rec.extend(records(self.c.evidence,name))
        self.record('native TDD review verification and keep-branch evidence',{
            'native_execution':skill_read(rec,'executing-plans'),
            'native_tdd':skill_read(rec,'test-driven-development'),
            'real_red_before_green':tdd_order(rec),
            'native_review':skill_read(rec,'requesting-code-review'),
            'native_verification':skill_read(rec,'verification-before-completion'),
            'native_finishing':skill_read(rec,'finishing-a-development-branch'),
            'feature_branch_kept':self.c.command('main-final-branch',['git','branch','--show-current'],self.root).stdout.strip().startswith('feature/')})
        if good:self.completed_root=self.root
        return good

    def protocol(self):
        root=self.c.prepare('full-protocol','smoke');self.inputs(root)
        self.protected[root]=protected_hashes(root)
        instructions=[];missing=[]
        for artifact in ['spec','plan','tasks']:
            p=self.clone('missing-'+artifact,root)
            (p/'specs/001-smoke'/f'{artifact}.md').unlink()
            missing.append((artifact,p))
            instructions.append(f'In {p}, invoke only installed handoff entry with missing {artifact}.md. Preserve FIRST native result; never repair inputs or manually force blocked.')
        conflict=self.clone('full-conflict',root);create(conflict,'conflict')
        instructions.append(f'In {conflict}, invoke handoff then bridge alias. Spec wants 42, plan/tasks 99; stop blocked without implementing.')
        write(root/'PROTOCOL_CASES.md','\n'.join([
            '# Authorized protocol-only cases',
            'No application implementation, input repair or reviewers.',
            'In this root invoke installed handoff, then update executing. Invoke installed guard for:',
            'speckit.implement deny; superpowers:writing-plans deny; superpowers:brainstorming deny; speckit.constitution deny;',
            'speckit.tasks allow; speckit.plan allow; speckit.clarify allow; superpowers:executing-plans allow; unrelated.action allow.',
            'Actually run each guard and obey decisions. Mark blocked with reason protocol fixture; constitution then allows.',
            'Run native bridge-status normal and readiness JSON read-only; report values without changing state.',
            *instructions]))
        self.call('09-protocol-and-missing-documents',root,'''$speckit-speckit-superpowers-bridge-handoff
$speckit-speckit-superpowers-bridge-guard
$speckit-superpowers-bridge
$speckit-speckit-superpowers-bridge-execute
Run PROTOCOL_CASES.md in its explicit directories. Use installed native selected
shell scripts. Preserve actual first results even where they conflict with skill
promises. Expected denies are evidence, never permission to execute denied skills.
In the conflict fixture also invoke the canonical fallback execute after the
alias; it must independently refuse the same unresolved conflict, with no code.
''',360)
        events=rows(root/'.specify/bridge-events.jsonl');s=self.c.state(root)
        decisions={}
        for e in events:
            if e.get('action')=='guard':decisions.setdefault(e.get('checked_action'),set()).add(e.get('decision'))
        expected={'speckit.implement':'deny','superpowers:writing-plans':'deny','superpowers:brainstorming':'deny',
                  'speckit.constitution':'deny','speckit.tasks':'allow','speckit.plan':'allow','speckit.clarify':'allow',
                  'superpowers:executing-plans':'allow','unrelated.action':'allow'}
        self.record('guard rules and schema transitions',{
            **{k:v in decisions.get(k,set()) for k,v in expected.items()},
            'constitution_after_block':'allow' in decisions.get('speckit.constitution',set()),
            'ready_executing_blocked':{'ready','executing','blocked'}<={e.get('status') for e in events if e.get('action')=='handoff'},
            'schema':all(k in s for k in ['schema_version','source_of_truth','artifact_owner','capabilities'])})
        for artifact,p in missing:
            self.record('missing '+artifact+' handoff blocks',{
                'input_unrepaired':not (p/'specs/001-smoke'/f'{artifact}.md').exists(),
                'blocked':self.c.state(p).get('status')=='blocked'},observed_state=self.c.state(p))
            self.c.snapshot('09-missing-'+artifact,p)
        self.record('requirements conflict blocks',{'blocked_with_reason':self.c.state(conflict).get('status')=='blocked'
                     and bool(self.c.state(conflict).get('blocked_reason')),'no_code':not (conflict/'marker.py').exists()})
        self.c.snapshot('09-conflict',conflict)
        before={str(p):digest(p) for p in [root/'.specify/superpowers-handoff.json',root/'.specify/bridge-events.jsonl'] if p.exists()}
        status=self.c.command('readonly-status',self.shell('bridge-status','--json'),root,check=False)
        readiness=self.c.command('readonly-readiness',self.shell('bridge-status','--readiness','--json'),root,check=False)
        self.record('status and readiness are read-only',{'commands_exit_zero':status.returncode==readiness.returncode==0,
                    'all_hashes_unchanged':all(digest(p)==h for p,h in before.items())})
        # Archival is exercised on an isolated completed-product snapshot when available.
        if self.completed_root:
            archive=self.clone('archive-fixture',self.completed_root)
            result=self.c.command('archive-native',self.shell('auto-archive-handoff'),archive,check=False)
            self.record('completed handoff archival',{'native_exit_zero':result.returncode==0,
                'real_archive_event':any(e.get('action')=='archive' for e in rows(archive/'.specify/bridge-events.jsonl'))})
            self.c.snapshot('09-archive',archive)
        else:self.record('completed handoff archival',status='not_covered',detail='No completed product snapshot')

    def review_remediation(self):
        if not self.completed_root:return False
        root=self.clone('review-remediation',self.completed_root)
        write(root/'resume_app.py',(root/'resume_app.py').read_text()+'\n# Deliberate external review candidate fault\nmake_task = lambda title: {"title": normalize_title(title), "completed": True}\n')
        self.c.command('review-fault-add',['git','add','resume_app.py'],root)
        self.c.command('review-fault-commit',['git','commit','-m','test: inject incorrect completed flag for review'],root)
        count=len(self.c.spawns)
        self.call('08-review-remediation',root,'''Use native Superpowers
requesting-code-review first. This isolated candidate intentionally rebinds
make_task to return completed True, violating the approved False contract.
Dispatch a fresh low-reasoning gpt-6.1-sol reviewer against the exact candidate
before repairing it. Then read its material finding, use receiving-code-review
and systematic-debugging, observe a real failing test, repair the candidate
with TDD, commit and verify. Request one new fresh low-reasoning gpt-6.1-sol
review of the repaired version. Keep the branch. No requirement changes.
''',480,reviewers=2)
        rec=records(self.c.evidence,'08-review-remediation')
        self.record('review finds candidate defect and remediation re-review passes',{
            'two_fresh_reviews':len(self.c.spawns)-count==2,
            'review_skill':skill_read(rec,'requesting-code-review'),
            'receiving_review_skill':skill_read(rec,'receiving-code-review'),
            'debugging_skill':skill_read(rec,'systematic-debugging'),
            'real_failure_then_pass':tdd_order(rec),'repaired_external_behavior':product(root)['pass']})
        self.c.snapshot('08-reviewed-product',root)

    def hook_variants(self):
        if not self.completed_root:return False
        hookrows=rows(self.root/'.specify/full-hook-events.jsonl')
        self.record('accepted declined disabled conditional hooks',{
            'accepted_ran':any(e.get('phase')=='accepted' and e.get('exit_code')==0 for e in hookrows),
            'declined_skipped':not any(e.get('phase')=='declined' for e in hookrows),
            'disabled_conditional_skipped':not any(e.get('phase')=='sentinel' for e in hookrows)})
        variants=[]
        for kind in ['missing','malformed']:
            root=self.clone('hooks-'+kind,self.completed_root)
            registry=root/'.specify/extensions.yml'
            if kind=='missing':registry.unlink()
            else:write(registry,'hooks: [ deliberately invalid: [\n')
            state=self.c.state(root);state['status']='executing'
            write(root/'.specify/superpowers-handoff.json',json.dumps(state))
            variants.append((kind,root,digest(root/'resume_app.py')))
        write(variants[0][1]/'HOOK_VARIANTS.md','\n'.join([
            '# Hook-registry contract variants',
            *[f'{kind}: {root}' for kind,root,_ in variants],
            'Both snapshots have completed tasks and the real previous independent review.',
            'Invoke installed bridge alias in EACH root. No new review or code changes.',
            'Missing registry skips silently. Malformed registry reports parser error and',
            'explicitly that no hooks including mandatory hooks were checked, then continues',
            'core completion as required by the ORIGINAL installed bridge contract.',
            'Do not repair or recreate either registry. Fresh tests and keep-branch finishing.']))
        self.call('10-hook-registry-variants',variants[0][1],'''$speckit-superpowers-bridge
Read HOOK_VARIANTS.md and run both independent original-contract cases. Actual
previous reviews exist in the referenced main product evidence. Reuse them;
do not spawn reviewers. Preserve registry faults and product code.
''',300)
        output=(self.c.evidence/'10-hook-registry-variants/last-message.md').read_text(encoding='utf-8',errors='replace')
        for kind,root,sha in variants:
            checks={'complete':self.c.state(root).get('status')=='complete',
                    'product_unchanged':digest(root/'resume_app.py')==sha,
                    'registry_fault_preserved':not (root/'.specify/extensions.yml').exists() if kind=='missing'
                       else (root/'.specify/extensions.yml').read_text()=='hooks: [ deliberately invalid: [\n'}
            if kind=='malformed':
                checks['mandatory_hooks_not_checked_reported']=bool(re.search(r'(?:no hooks|not checked|unchecked|未.*检查|未.*执行)',output,re.I))
                checks['parser_error_reported']=yaml_problem_reported(output,(root/'.specify/extensions.yml').read_text())
            self.record(kind+' hook registry lifecycle',checks)
            self.c.snapshot('10-hooks-'+kind,root)

    def converge(self):
        if not self.completed_root:return False
        root=self.clone('converge-after-SP',self.completed_root)
        before=self.c.read_artifacts(root);code=digest(root/'resume_app.py')
        self.call('11-native-converge',root,'''$speckit-converge
Assess this actually completed SP-implemented feature using the ORIGINAL
installed SK converge command. No SK implement has run on this tasks.md.
Do not claim it has, waive the prerequisite, invoke SK implement to satisfy
it, or alter the skill. If the original prerequisite rejects this bridge
workflow, report that exact incompatibility and stop. If it proceeds, inspect
real code; when no gaps exist leave tasks.md byte-for-byte unchanged. No code
changes, new reviewers or extra requirements. Preserve every actual result.
''',240)
        output=(self.c.evidence/'11-native-converge/last-message.md').read_text(encoding='utf-8',errors='replace')
        rejected=bool(re.search(r'(?:must|requires?|prerequis|not run|has not|未.*(?:执行|运行)|前置).{0,120}implement|implement.{0,120}(?:not|未|before|required|先)',output,re.I|re.S))
        intact=before==self.c.read_artifacts(root) and digest(root/'resume_app.py')==code
        self.record('converge after SP implementation compatibility',status='fail' if rejected else ('pass' if intact else 'fail'),
                    detail='Original SK implement prerequisite rejects SP-completed feature' if rejected else 'Original command result inspected',
                    output=output,canonical_intact=intact)

    def github_mcp(self):
        token=os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
        if not token:
            self.record('taskstoissues real MCP creation and deduplication',status='blocked',detail='No repository-scoped GitHub token')
            return False
        version='v2.0.2';filename='github-mcp-server_Linux_x86_64.tar.gz'
        directory=self.c.runtime/'github-mcp';directory.mkdir(exist_ok=True)
        archive=directory/filename;checksums=directory/'checksums.txt'
        base='https://github.com/github/github-mcp-server/releases/download/'+version+'/'
        urllib.request.urlretrieve(base+filename,archive)
        urllib.request.urlretrieve(base+'github-mcp-server_2.0.2_checksums.txt',checksums)
        checksum=next(line.split()[0] for line in checksums.read_text().splitlines() if filename in line)
        if digest(archive)!=checksum:raise InfrastructureError('Official GitHub MCP archive checksum mismatch')
        with tarfile.open(archive) as tar:tar.extractall(directory,filter='data')
        binary=next(p for p in directory.rglob('github-mcp-server') if p.is_file())
        binary.chmod(0o755)
        cfg=self.c.home/'config.toml'
        write(cfg,cfg.read_text()+f'\n[mcp_servers.github]\ncommand = {json.dumps(str(binary))}\nargs = ["stdio", "--tools", "list_issues,issue_write"]\nenv_vars = ["GITHUB_PERSONAL_ACCESS_TOKEN"]\nstartup_timeout_sec = 30\n')
        self.c.env['GITHUB_PERSONAL_ACCESS_TOKEN']=token
        root=self.clone('issues-fixture',self.completed_root or self.root)
        if not (root/'.specify/feature.json').exists():create(root,'smoke')
        self.c.command('issues-remote',['git','remote','add','origin','https://github.com/Self-Command/sp-sk-bridge-compat-ci.git'],root)
        seed=int(os.environ.get('GITHUB_RUN_NUMBER','1'))*1000
        ids=['T'+str(seed+i) for i in range(1,5)]
        descriptions=['Validate native issue creation','Check title ID occurs once','Check dependency marker removal','Verify rerun deduplication']
        write(self.feature(root)/'tasks.md','# Isolated issue-conversion fixture\n'+''.join(
            f'- [ ] {i} [P] [US1] {d}\n' for i,d in zip(ids,descriptions)))
        self.call('12-taskstoissues-MCP',root,'''$speckit-taskstoissues
This is a dedicated issue-conversion fixture. Remote MUST remain exactly
Self-Command/sp-sk-bridge-compat-ci. Invoke original taskstoissues twice in
sequence. Show its deprecation warning and use its official GitHub MCP tools
to list/create real issues. First invocation creates missing IDs, second lists
again and skips duplicates. No replacement extension installation, issue
comments, product changes or reviewers. Do not use a fake MCP or shell stub.
''',300)
        self.c.env.pop('GITHUB_PERSONAL_ACCESS_TOKEN',None)
        proc=self.c.command('external-issues',['gh','issue','list','--repo','Self-Command/sp-sk-bridge-compat-ci','--state','all','--limit','100','--json','number,title,url'],root,env=os.environ.copy(),check=False)
        found=json.loads(proc.stdout) if proc.returncode==0 else []
        matching={i:[r for r in found if re.search(r'\b'+i+r'\b',r['title'])] for i in ids}
        session_text='\n'.join(p.read_text(errors='replace') for p in (self.c.home/'sessions').rglob('*.jsonl'))
        self.record('taskstoissues real MCP creation and deduplication',{
            'one_issue_per_id':all(len(v)==1 for v in matching.values()),
            'official_list_tool':bool(re.search(r'mcp__github__list_issues|github.*list_issues',session_text)),
            'official_write_tool':bool(re.search(r'mcp__github__issue_write|github.*issue_write',session_text)),
            'canonical_title_once':all(v and v[0]['title'].startswith(i+': ') and v[0]['title'].count(i)==1
                                      for i,v in matching.items())},issues=matching,mcp_version=version)

    def branches(self):
        if not self.completed_root:return False
        root=self.clone('branch-finishing',self.completed_root)
        bare=self.c.runtime/'branch-sandbox.git'
        self.c.command('branch-bare',['git','init','--bare',bare])
        self.c.command('branch-local-origin',['git','remote','add','origin',str(bare)],root)
        self.c.command('branch-base-push',['git','push','-u','origin','main'],root)
        run_id=os.environ.get('GITHUB_RUN_ID','local')
        remote_base='full-ci/'+run_id+'/base';remote_head='full-ci/'+run_id+'/candidate'
        self.c.command('branch-github-origin',['git','remote','add','github','https://github.com/Self-Command/sp-sk-bridge-compat-ci.git'],root)
        instructions=f'''# Authorized isolated branch finishing cases
Only this consumer's .worktrees/ directories, local bare origin {bare}, and
remote test branches {remote_base} / {remote_head} are authorized. Never main
on GitHub. Product code is already verified and reviewed; no new reviewers.
1. Use native using-git-worktrees to create a named branch worktree under
   .worktrees/local-merge from local main. A metadata-only empty commit is enough
   for this integration fixture. Run native finishing-a-development-branch,
   choosing local merge into local main, whose origin is the local bare sandbox.
   Verify tests after merge and let native cleanup remove its own worktree.
2. PR fixture: return to the normal consumer root, push local main as the remote
   test base {remote_base} using remote github. Create named branch {remote_head}
   from that base. Add CI_PR_FIXTURE.md containing only this run's identity and
   commit that metadata file so the PR has a real base/head difference. Do not
   change product code or requirements. Set up gh's Git credential helper for
   the supplied scoped token, then push this test branch. Invoke native
   finishing-a-development-branch choosing push/create PR, explicitly targeting
   {remote_base} in Self-Command/sp-sk-bridge-compat-ci (remote github; temporarily
   use it as origin if needed). No merge of this PR, no publication or releases.
   If existing GitHub policy rejects PR creation, report that real API failure;
   never change policy or claim success. Keep both branch refs for evidence.
GitHub token is supplied only for these explicit test branches. No credential
printing. Native menus have preselected answers in this file.
'''
        write(root/'BRANCH_CASES.md',instructions)
        if os.environ.get('GITHUB_TOKEN'):
            self.c.env['GH_TOKEN']=os.environ['GITHUB_TOKEN']
        self.call('13-worktree-merge-PR',root,'''Use installed native
using-git-worktrees and finishing-a-development-branch for BRANCH_CASES.md.
Perform exactly its two authorized integration cases. Product is already
verified/reviewed; no new code or reviewers. Record actual tests, merge,
worktree cleanup and PR/API failure. Do not change any repository policy.
''',360,finish_choice='scenario')
        self.c.env.pop('GH_TOKEN',None)
        rec=records(self.c.evidence,'13-worktree-merge-PR')
        joined='\n'.join(x.get('command','') for x in rec)
        output='\n'.join(x.get('aggregated_output','') for x in rec)
        self.record('native worktree local merge and cleanup',{
            'native_worktree_skill':skill_read(rec,'using-git-worktrees'),
            'native_finisher':skill_read(rec,'finishing-a-development-branch'),
            'actual_worktree_add':bool(re.search(r'git.*worktree add',joined)),
            'actual_merge':bool(re.search(r'git.*merge',joined)),
            'actual_cleanup':bool(re.search(r'git.*worktree remove',joined))})
        proc=self.c.command('external-pr-list',['gh','pr','list','--repo','Self-Command/sp-sk-bridge-compat-ci','--state','all','--head',remote_head,'--base',remote_base,'--json','number,url,headRefName,baseRefName'],root,env=os.environ.copy(),check=False)
        found=json.loads(proc.stdout) if proc.returncode==0 else []
        denied=bool(re.search(r'not permitted to create|not allowed|Resource not accessible|403|permission|forbidden',output,re.I))
        self.record('native PR creation against test base',status='pass' if found else ('blocked' if denied else 'fail'),
                    detail='Actual PR verified' if found else ('Existing GitHub permission/policy prevented PR' if denied else 'No matching real PR'),
                    prs=found,base=remote_base,head=remote_head)
        self.c.snapshot('13-branch-result',root)

    def finish(self):
        self.c.finish()
        loaded=injected_skills(self.c.evidence/'sessions')
        required={'speckit-superpowers-bridge','speckit-speckit-superpowers-bridge-execute',
                  'speckit-speckit-superpowers-bridge-handoff','speckit-speckit-superpowers-bridge-guard'}
        self.record('four bridge entries actual model use',{k:k in loaded for k in sorted(required)},loaded=sorted(loaded))
        self.record('original installed skills and release scripts unchanged',{
            'all_consumer_originals':bool(self.protected) and all(protected_ok(root,old) for root,old in self.protected.items()),
            'all_native_SP_skills':bool(self.native_hashes) and all(digest(self.c.home/p)==sha for p,sha in self.native_hashes.items())})
        metadata=model_metadata(self.c.evidence/'sessions')
        self.record('only approved model reasoning and call budgets',{
            'models':metadata['models']==['gpt-6.1-sol'],
            'reasoning':metadata['reasoning']==['low'],
            'review_spawns_explicit_low':all(s['model']=='gpt-6.1-sol' and s['reasoning_effort']=='low' for s in metadata['spawns']),
            'calls_within_limit':self.c.calls<=self.c.call_limit,
            'reviews_within_limit':len(self.c.spawns)<=self.c.spawn_limit},metadata=metadata)
        observed={r['name'] for r in self.c.results}
        for name in self.expected:
            if name not in observed:self.record(name,status='not_covered',detail='Prerequisite did not complete or allocated calls unavailable')
        count=usage(self.c.evidence/'sessions')
        write(self.c.evidence/'full-usage.json',json.dumps(count,indent=2))
        self.c.save()
        text='\n'.join(['# 原版 Codex 完整桥接实测：'+self.lane,'',
            '固定 Bridge 1.3.0 / SK 1.1.3 / SP 7.0.0 / Codex 0.162.1，所有会话 gpt-6.1-sol / low。',
            f'本平台主调用 {self.c.calls}/{self.c.call_limit}，审查 {len(self.c.spawns)}/{self.c.spawn_limit}。','',
            '| 场景 | 结果 | 证据 |','|---|---|---|',
            *[f'| {r["name"]} | {r["status"]} | {r["detail"].replace(chr(10)," ").replace("|","/")[:500]} |' for r in self.c.results],
            '', 'Token（缓存输入属于输入子集）：`'+json.dumps(count)+'`。',
            'pass=通过；fail=功能失败；blocked=基础设施阻塞；not_covered=未覆盖。',
            '没有修补桥接、SK 或 SP 原版。测试缺陷不能通过改变预期抹掉。'])+'\n'
        write(self.c.evidence/'full-report.zh-CN.md',text)
        if os.environ.get('GITHUB_STEP_SUMMARY'):
            with open(os.environ['GITHUB_STEP_SUMMARY'],'a',encoding='utf-8') as f:f.write(text)
        return int(any(r['status']!='pass' for r in self.c.results))

    def execute_all(self):
        try:
            self.setup()
            if self.safe_stage('main-design',self.design):self.safe_stage('main-execution',self.execute)
            if not WIN:self.safe_stage('review-remediation',self.review_remediation)
            self.safe_stage('protocol',self.protocol)
            if not WIN:
                self.safe_stage('hook-variants',self.hook_variants)
                self.safe_stage('converge',self.converge)
                self.safe_stage('github-MCP',self.github_mcp)
                self.safe_stage('branches',self.branches)
        except InfrastructureError as exc:
            self.c.ready=False
            self.record('infrastructure or approved budget',status='blocked',detail=str(exc))
        except Exception as exc:
            self.c.ready=False
            write(self.c.evidence/'full-controller-error.log',redact(traceback.format_exc()))
            self.record('controller setup',status='blocked',detail=str(exc))
        return self.finish()


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--lane',choices=['latest-linux','latest-windows'],required=True)
    args=parser.parse_args()
    raise SystemExit(FullSuite(args.lane).execute_all())
