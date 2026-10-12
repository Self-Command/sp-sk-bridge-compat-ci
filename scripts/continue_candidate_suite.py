"""Continue only unfinished candidate scenarios, retaining every paid call.

Text snapshots restore the actual model-generated product and canonical files.
Native upstream/bridge files are reinstalled and checked from the same immutable
candidate, never reconstructed from sanitized evidence. Original Git commits
remain evidenced by their logs/rollouts; restored checkouts get an explicitly
named restoration commit rather than pretending to recreate those commits.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil

from fixtures import write
from full_verify import (contract_ok, model_metadata, product, protected_hashes,
                         records, skill_read, test_suite, tests_pass)
from run_ci import InfrastructureError, WIN
from run_candidate_suite import CandidateSuite
from run_full_suite import HOOK_SCRIPT
from sanitize import redact
from suite_verify import rows, tdd_order
from verify import digest, tasks


class ContinuedCandidate(CandidateSuite):
    def __init__(self,lane,prior):
        self.prior=Path(prior)
        self.previous=json.loads((self.prior/'results.json').read_text())
        self.expected_prior={'latest-linux':(9,2),'latest-windows':(2,1)}[lane]
        assert (self.previous['model_calls'],self.previous['reviewer_spawns'])==self.expected_prior
        self.previous_versions=json.loads((self.prior/'versions.json').read_text())
        super().__init__(lane)
        for path in self.prior.rglob('*'):
            if path.is_file():
                dest=self.c.evidence/path.relative_to(self.prior)
                dest.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(path,dest)
        write(self.c.evidence/'previous-results.json',json.dumps(self.previous,indent=2))
        # Retain paid/process evidence. Missing prerequisites will be assessed
        # anew; a named regrade log records each corrected checker outcome.
        reassess={'fresh-session post-hook recovery does not rewrite product',
                  'main product external acceptance and task completion',
                  'native TDD review verification and keep-branch evidence',
                  'new convergence entry actually loaded'}
        if WIN:reassess.add('SP brainstorming produces PRD with real builder check')
        else:reassess.add('systematic debugging repairs injected completed-task fault')
        self.c.results=[row for row in self.previous['scenarios']
                        if row['status']!='not_covered' and row['name'] not in reassess]
        self.c.calls=self.previous['model_calls']
        for path in (self.prior/'sessions').rglob('*.jsonl'):
            dest=self.c.home/'sessions'/path.relative_to(self.prior/'sessions')
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(path,dest)
        self.c.scan_sessions()
        assert len(self.c.spawns)==self.previous['reviewer_spawns']
        self.c.save()

    def restore(self,snapshot):
        for path in snapshot.rglob('*'):
            if not path.is_file():continue
            relative=path.relative_to(snapshot).as_posix()
            if relative.startswith(('.specify/extensions/speckit-superpowers-bridge/',
                                    '.specify/scripts/')):
                continue
            if relative.startswith('.agents/skills/') and not relative.startswith('.agents/skills/speckit-ci-'):
                continue
            dest=self.root/path.relative_to(snapshot)
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(path,dest)
        self.inputs(self.root)
        self.c.command('restored-evidence-add',['git','add','.'],self.root)
        self.c.command('restored-evidence-commit',['git','commit','-m','test: restore actual prior model snapshot; original commit evidence retained'],self.root)
        self.protected[self.root]=protected_hashes(self.root)

    def setup(self):
        super().setup()
        assert self.c.candidate_index==self.previous_versions['candidate'],'Continuation package differs from original paid evidence'
        snapshot_name='01-brainstorm-prd' if WIN else '07-post-hook-recovery'
        snapshot=self.prior/snapshot_name/'snapshot'
        self.restore(snapshot)
        detail={'source_run':38283007683,'prior_calls':self.c.calls,
                'prior_reviewers':len(self.c.spawns),
                'snapshot':snapshot_name,'source_candidate':self.c.candidate_index,
                'product_source_unchanged':True,'canonical_documents_unchanged':True,
                'original_commit_evidence':'setup/*-git-log.log and original rollouts',
                'restored_git_commit':'Explicit snapshot restoration, not an original implementation commit'}
        if WIN:
            original=(self.c.sources['superpowers']/'skills/brainstorming/SKILL.md').read_text()
            rec=records(self.c.evidence,'01-brainstorm-prd')
            prd=self.root/'docs/product/title-task-prd.md'
            self.record('SP brainstorming produces PRD with real builder check',{
                'prd_written':prd.stat().st_size>150,
                'approved_interfaces_present':all(x in prd.read_text() for x in ['normalize_title','make_task','resume_app.py']),
                'builder_review_spawned':self.previous['reviewer_spawns']==1,
                'native_brainstorming_read':skill_read(rec,'brainstorming',original),
                'no_application_before_SK':not (self.root/'resume_app.py').exists()},
                regrade='Full pinned native skill body exists in tool output; a subsequent rg command made the batch exit 1.')
        else:
            self.original_artifacts=self.c.read_artifacts(self.prior/'03-sk-tasks-checklist-analyze/snapshot')
            self.original_tasks=(self.prior/'03-sk-tasks-checklist-analyze/snapshot'/self.feature(self.root).relative_to(self.root)/'tasks.md').read_text()
            assert contract_ok(self.original_artifacts,self.c.read_artifacts(self.root))
            self.main_call_names=['05-interrupt-after-task1','06-resume-debug-post-failure']
            self.main_tasks_base=self.c.command('restored-base',['git','rev-parse','HEAD'],self.root).stdout.strip()
            # The original SK plan chose root test_resume_app.py. Correct only
            # the external synthetic hook's erroneous hardcoded tests/ path.
            previous_hook=digest(self.root/'ci_hooks/record.py')
            write(self.root/'ci_hooks/record.py',HOOK_SCRIPT)
            detail['external_hook_repair']={'previous_sha256':previous_hook,
                'current_sha256':digest(self.root/'ci_hooks/record.py'),
                'reason':'Follow generated project test layout and require a real nonempty suite'}
            rec=records(self.c.evidence,'06-resume-debug-post-failure')
            self.record('systematic debugging repairs injected completed-task fault',{
                'native_debugging_used':skill_read(rec,'systematic-debugging'),
                'actual_failed_then_passed_tests':tdd_order(rec),
                'repaired_behavior':product(self.root)['pass']},
                regrade='Actual nonempty unittest FAILED then OK in batched output; later shell command returned 0.')
            detail['canonical_appendix_regrade']='Exact original prefix and original requirements preserved; additional recovery/review headings contain observed test evidence without new tasks or normative requirements.'
        write(self.c.evidence/'continuation-provenance.json',json.dumps(detail,indent=2))
        self.c.ready=True

    def remaining_design(self):
        # Reuse the exact original SK design/tasks prompts without repeating
        # the already proved PRD or its paid builder check.
        for name,timeout in [('02-sk-design',360),('03-sk-tasks-checklist-analyze',360)]:
            prompt=(Path(__file__).resolve().parents[1]/'scripts/run_full_suite.py').read_text()
            start=prompt.index("self.call('"+name+"',self.root,'''" )
            body=prompt[start:].split("'''",2)[1]
            self.call(name,self.root,body,timeout)
            if name=='02-sk-design':
                feature=self.feature()
                if not self.record('SK generates approved constitution spec and plan',{
                    'all_documents':all(p.exists() and p.stat().st_size>100 for p in [self.root/'.specify/memory/constitution.md',feature/'spec.md',feature/'plan.md']),
                    'no_product_yet':not (self.root/'resume_app.py').exists()}):return False
            else:
                feature=self.feature();items=tasks(feature/'tasks.md');state=self.c.state(self.root)
                if not self.record('SK three tasks checklist analysis and automatic handoff',{
                    'three_pending_ids':[(t[0],t[1]) for t in items]==[('T001',False),('T002',False),('T003',False)],
                    'automatic_ready':state.get('status')=='ready',
                    'automatic_event':any(e.get('action')=='handoff' and e.get('status')=='ready' for e in rows(self.root/'.specify/bridge-events.jsonl')),
                    'checklist_artifact':any(p.stat().st_size>80 for p in (feature/'checklists').glob('*.md')),
                    'no_application_before_bridge':not (self.root/'resume_app.py').exists()}):return False
                self.original_artifacts=self.c.read_artifacts(self.root)
                self.original_tasks=(feature/'tasks.md').read_text()
                self.hooks(self.root)
                self.main_tasks_base=self.c.command('main-base',['git','rev-parse','HEAD'],self.root).stdout.strip()
        return True

    def recover_completed_linux(self):
        # Free precheck before spending the only remaining recovery call.
        assert tests_pass(test_suite(self.root)) and product(self.root)['pass']
        before={str(p.relative_to(self.root)):digest(p) for p in self.root.rglob('*.py')
                if p.name=='resume_app.py' or p.name.startswith('test_')}
        prior=len(self.c.spawns)
        write(self.root/'CI_CONTINUATION.md',f'''# Actual retained evidence
Previous complete independent review, product fixes and test runs are recorded at
{self.c.evidence / '06-resume-debug-post-failure'} and {self.c.evidence / 'sessions'}.
The controller corrected only the external synthetic post-hook test-discovery
path: the canonical SK plan chose root test_resume_app.py; the old hook hardcoded
tests/. The completed product and original task contract were preserved.
Git history is a snapshot-restoration commit; original actual task commits are
preserved in exported git logs and rollouts, not invented as new commits.
''')
        self.call('14-retained-post-hook-recovery',self.root,'''$speckit-superpowers-bridge
Read CI_CONTINUATION.md. The same canonical three tasks and actual product are
already complete; the previous version received a real independent review.
Only the external synthetic post-hook had a wrong test start path; it has been
corrected to run the documented root unittest suite. Reuse the actual prior
review. Run mandatory post-hook and fresh verification/keep-branch finishing,
then complete. No reviewers, repeated tasks, product changes or requirement
changes. Record only actual successful completion evidence.
If recording it in tasks.md, append factual results under a T### execution
evidence heading; do not rewrite any existing requirement, task or evidence.
''',300)
        self.main_call_names.append('14-retained-post-hook-recovery')
        self.record('fresh-session post-hook recovery does not rewrite product',{
            'complete':self.c.state(self.root).get('status')=='complete',
            'code_tests_unchanged':all(digest(self.root/p)==sha for p,sha in before.items()),
            'no_new_reviewer':len(self.c.spawns)==prior,
            'actual_successful_post':any(e.get('phase')=='post' and e.get('exit_code')==0 for e in rows(self.root/'.specify/full-hook-events.jsonl'))})
        if not self.main_acceptance():return False
        archive=self.clone('continued-archive',self.completed_root)
        result=self.c.command('continued-archive-native',self.shell('auto-archive-handoff'),archive,check=False)
        self.record('completed handoff archival',{
            'native_exit_zero':result.returncode==0,
            'real_archive_event':any(e.get('action')=='archive' for e in rows(archive/'.specify/bridge-events.jsonl'))})
        self.c.snapshot('14-completed-product',self.root)
        return True

    def execute_all(self):
        try:
            self.setup()
            if WIN:
                if self.safe_stage('remaining-design',self.remaining_design):
                    self.safe_stage('remaining-execute',self.execute)
                    if self.completed_root:
                        archive=self.clone('continued-archive',self.completed_root)
                        result=self.c.command('continued-archive-native',self.shell('auto-archive-handoff'),archive,check=False)
                        self.record('completed handoff archival',{
                            'native_exit_zero':result.returncode==0,
                            'real_archive_event':any(e.get('action')=='archive' for e in rows(archive/'.specify/bridge-events.jsonl'))})
                        self.safe_stage('converge',self.converge)
            elif self.safe_stage('remaining-recovery',self.recover_completed_linux):
                for name,fn in [('review-remediation',self.review_remediation),('hook-variants',self.hook_variants),
                                ('converge',self.converge),('branches',self.branches)]:
                    self.safe_stage(name,fn)
        except InfrastructureError as exc:
            self.c.ready=False
            self.record('infrastructure or approved cumulative budget',status='blocked',detail=str(exc))
        except Exception as exc:
            import traceback
            write(self.c.evidence/'continuation-error.log',redact(traceback.format_exc()))
            self.record('continuation controller',status='blocked',detail=f'{type(exc).__name__}: {exc}')
        return self.finish()


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--lane',choices=['latest-linux','latest-windows'],required=True)
    parser.add_argument('--prior',type=Path,required=True)
    args=parser.parse_args()
    raise SystemExit(ContinuedCandidate(args.lane,args.prior).execute_all())
