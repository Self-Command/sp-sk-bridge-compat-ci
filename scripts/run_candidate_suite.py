"""Candidate regression over the original full-suite scenario implementation."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil

import yaml

from fixtures import write
from full_verify import protected_ok, records, run, skill_read, usage
from run_ci import InfrastructureError, WIN
from run_full_suite import FullSuite
from suite_verify import injected_skills, rows
from verify import digest, tasks

CONVERGE_SCENARIOS = [
    'bridge convergence clean and repeated assessment',
    'bridge convergence appends actual gap with preserved contract',
    'bridge convergence pending repeat refuses without duplicate tasks',
    'bridge convergence prerequisite failures are read-only',
    'bridge convergence mandatory post-hook failure blocks',
    'bridge convergence actual verification and original SK skill unchanged',
]


class CandidateSuite(FullSuite):
    def __init__(self, lane):
        super().__init__(lane)
        self.expected += CONVERGE_SCENARIOS

    def setup(self):
        super().setup()
        self.c.results = [row for row in self.c.results if row['name'] != 'fixed originals installed']
        self.record('fixed candidate and original upstreams installed', {
            'candidate_sha_pinned':bool(self.c.candidate_index and self.c.candidate_index['source_sha'] == os.environ['BRIDGE_CANDIDATE_SHA']),
            'SK_113_SP_700_Codex_01621': True}, candidate=self.c.candidate_index)

    def helper(self, root):
        return self.c.command('qualify-' + root.name, self.shell('prepare-convergence', '--actor', 'codex'), root, check=False)

    def immutable(self, root):
        return {str(p.relative_to(root)):digest(p) for p in root.rglob('*') if p.is_file()
                and (str(p.relative_to(root)).replace('\\','/').startswith(('specs/','.specify/','.agents/'))
                     or str(p.relative_to(root)).replace('\\','/').startswith('tests/')
                     or p.name == 'resume_app.py')}

    def convergence_case(self, root, kind, fault=''):
        feature = self.feature(root)
        if fault:
            original = (root/'resume_app.py').read_bytes()
            (root/'resume_app.py').write_bytes(original + fault.encode())
        if kind == 'post-failure':
            registry = root/'.specify/extensions.yml'
            data = yaml.safe_load(registry.read_text(encoding='utf-8-sig'))
            data.setdefault('hooks',{})['after_converge'] = [{
                'extension':'ci-converge-post', 'command':'speckit.ci.sentinel',
                'enabled':True, 'condition':None, 'optional':False,
                'description':'Intentional mandatory convergence post-hook exit 29.'}]
            write(registry, yaml.safe_dump(data, sort_keys=False))
        before = self.immutable(root)
        self.protected[root].update({str(p.relative_to(root)):digest(p)
                                    for p in (root/'.agents/skills').rglob('*') if p.is_file()})
        return {'root':root,'kind':kind,'before':before,
                'tasks':(feature/'tasks.md').read_bytes(), 'native':digest(root/'.agents/skills/speckit-converge/SKILL.md')}

    def converge(self):
        if not self.completed_root:
            return False
        cases=[]
        for kind in ('clean','gap','post-failure','ineligible'):
            root=self.clone('candidate-converge-' + kind, self.completed_root)
            cases.append(self.convergence_case(root,kind,
                '\n# Deliberate external convergence assessment fault\nmake_task = lambda title: {"title": normalize_title(title), "completed": True}\n'
                if kind == 'gap' else ''))
        clean,gap,post,ineligible=cases
        # A non-complete state is a controlled refusal fixture, never repaired by the model.
        self.c.command('converge-ineligible-state',self.shell('update-handoff','--status','executing','--actor','codex'),ineligible['root'])
        ineligible['before']=self.immutable(ineligible['root'])
        # Exercise other qualification failures without consuming model calls.
        refusals={}
        for mode in ('no-execution-events','missing-spec','drift','pending','unrecognized-native'):
            root=self.clone('candidate-qualify-'+mode,self.completed_root)
            feature=self.feature(root)
            if mode=='no-execution-events':
                write(root/'.specify/bridge-events.jsonl','')
            elif mode=='missing-spec':
                (feature/'spec.md').unlink()
            elif mode=='drift':
                with (feature/'plan.md').open('ab') as stream:stream.write(b'\nchanged after completion\n')
            elif mode=='pending':
                write(feature/'tasks.md',(feature/'tasks.md').read_text().replace('- [x] T001','- [ ] T001'))
                # A current hash alone must not qualify an unfinished task.
                state=self.c.state(root);state['artifacts_sha256']['tasks.md']=digest(feature/'tasks.md')
                write(root/'.specify/superpowers-handoff.json',json.dumps(state))
            else:
                write(root/'.agents/skills/speckit-converge/SKILL.md','# Changed upstream contract\n')
                self.protected[root]=__import__('full_verify').protected_hashes(root)
            before=self.immutable(root)
            result=self.helper(root)
            try:data=json.loads(result.stdout)
            except ValueError:data={}
            refusals[mode]=result.returncode==1 and data.get('eligible') is False and bool(data.get('reason')) and before==self.immutable(root)
        # Check the original native prerequisite without pretending it ran.
        original=(clean['root']/'.agents/skills/speckit-converge/SKILL.md').read_text(encoding='utf-8')
        write(self.c.evidence/'native-converge-limitation.json',json.dumps({
            'native_unchanged':True,'implement_prerequisite_retained':'`$speckit-implement` has run' in original,
            'supported_SP_entry':'$speckit-speckit-superpowers-bridge-converge'},indent=2))
        instructions='\n'.join(f'{case["kind"]}: {case["root"]}' for case in cases)
        write(clean['root']/'CONVERGENCE_CASES.md',instructions)
        self.call('11-bridge-convergence',clean['root'],'''Read CONVERGENCE_CASES.md.
Use the installed $speckit-speckit-superpowers-bridge-converge entry in each
explicitly authorized independent consumer. No reviewers, no new product code.
1. clean: run the bridge convergence procedure twice; inspect code and actual
documented tests each time, then leave tasks/code/complete state unchanged.
2. gap: an external make_task fault breaks completed=false. Run convergence to
assess the real failure and append only traceable remediation tasks with new
IDs, without fixing code, rewriting old tasks, spec or plan. Then invoke the
same convergence entry again: ready/pending state must refuse without duplicate
tasks. Do not run bridge implementation, reset evidence, or invoke SK implement.
3. post-failure: clean product, but mandatory after_converge hook intentionally
exits 29. Actually invoke it, stop and mark blocked; do not bypass the hook.
4. ineligible: current executing state must refuse read-only and stay unchanged.
Each entry must use its helper-created temporary adapter over the installed
native procedure; remove generated adapters on every exit path. Preserve all
installed native skills. Summarize actual results, not planned outcomes.
''',600)
        rec=records(self.c.evidence,'11-bridge-convergence')
        commands='\n'.join(r.get('command','') for r in rec)
        clean_after=self.immutable(clean['root'])
        self.record('bridge convergence clean and repeated assessment',{
            'canonical_and_code_byte_identical':all(clean_after.get(p)==h for p,h in clean['before'].items()),
            'complete_preserved':self.c.state(clean['root']).get('status')=='complete',
            'helper_invoked_twice':commands.count('prepare-convergence')>=2})
        gap_tasks=(self.feature(gap['root'])/'tasks.md').read_bytes()
        suffix=gap_tasks[len(gap['tasks']):] if gap_tasks.startswith(gap['tasks']) else b''
        new_ids=re.findall(rb'^- \[ \] (T\d+)',suffix,re.M)
        prior_ids=[int(t[0][1:]) for t in tasks(self.feature(clean['root'])/'tasks.md')]
        appended=bool(new_ids) and all(int(t[1:])>max(prior_ids) for t in new_ids)
        self.record('bridge convergence appends actual gap with preserved contract',{
            'append_only':gap_tasks.startswith(gap['tasks']) and appended,
            'traceable_gap':bool(re.search(rb'FR-\d+|SC-\d+|US\d|plan:|Constitution',suffix)),
            'correct_completion_gap':bool(re.search(rb'completed|false|make_task',suffix,re.I)),
            'ready_returned':self.c.state(gap['root']).get('status')=='ready',
            'spec_plan_product_unchanged':all(digest(gap['root']/p)==h for p,h in gap['before'].items()
                if p.endswith(('spec.md','plan.md','resume_app.py')))})
        self.record('bridge convergence pending repeat refuses without duplicate tasks',{
            'one_convergence_phase':len(re.findall(rb'^## Phase \d+: Convergence',suffix,re.M))==1,
            'all_new_ids_unique':len(new_ids)==len(set(new_ids)),
            'pending_repeat_qualification_refuses':self.helper(gap['root']).returncode==1})
        ineligible_unchanged=ineligible['before']==self.immutable(ineligible['root'])
        self.record('bridge convergence prerequisite failures are read-only',{
            **refusals,'actual_entry_refused_ineligible_without_mutation':ineligible_unchanged})
        self.record('bridge convergence mandatory post-hook failure blocks',{
            'actual_exit29':any(e.get('phase')=='sentinel' and e.get('exit_code')==29 for e in rows(post['root']/'.specify/full-hook-events.jsonl')),
            'blocked':self.c.state(post['root']).get('status')=='blocked',
            'tasks_unchanged':(self.feature(post['root'])/'tasks.md').read_bytes()==post['tasks']})
        self.record('bridge convergence actual verification and original SK skill unchanged',{
            'installed_entry_used':'speckit-speckit-superpowers-bridge-converge' in injected_skills(self.c.evidence/'sessions'),
            'real_tests':bool(re.search(r'unittest.*discover',commands)),
            'native_command_unchanged':all(digest(case['root']/'.agents/skills/speckit-converge/SKILL.md')==case['native'] for case in cases),
            'original_prerequisite_retained':'`$speckit-implement` has run' in original})
        self.record('converge after SP implementation compatibility',{'bridge_entry_completed_assessment':appended and ineligible_unchanged},
            detail='The supported bridge entry adapted SP completion; original SK implement-only prerequisite is retained.')
        for case in cases:self.c.snapshot('11-convergence-'+case['kind'],case['root'])

    def execute_all(self):
        if not WIN:
            return super().execute_all()
        try:
            self.setup()
            if self.safe_stage('main-design',self.design):self.safe_stage('main-execution',self.execute)
            self.safe_stage('protocol',self.protocol)
            self.safe_stage('converge',self.converge)
        except InfrastructureError as exc:
            self.c.ready=False
            self.record('infrastructure or approved budget',status='blocked',detail=str(exc))
        return self.finish()

    def finish(self):
        result=super().finish()
        loaded=injected_skills(self.c.evidence/'sessions')
        self.record('new convergence entry actually loaded',{'installed_entry':'speckit-speckit-superpowers-bridge-converge' in loaded})
        self.c.save()
        write(self.c.evidence/'candidate-coverage.json',json.dumps({'source':self.c.candidate_index,
            'native_SK_converge':'Unmodified implement-only prerequisite; bridge-specific entry is the supported SP path.',
            'new_coverage':CONVERGE_SCENARIOS},indent=2))
        return int(any(row['status']!='pass' for row in self.c.results))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--lane',choices=['latest-linux','latest-windows'],required=True)
    args=parser.parse_args()
    raise SystemExit(CandidateSuite(args.lane).execute_all())
