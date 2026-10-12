"""Real Codex controller: prepare inputs, invoke models, inspect outside worktrees.

No bridge or Superpowers implementation skill is executed by this controller.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import traceback
import urllib.request
import zipfile

from fixtures import CONSTITUTION, PRODUCT, create, write
from sanitize import redact, sanitize
from verify import digest, evidence_flags, immutable_artifacts, product, resume_product, tasks

ROOT = Path(__file__).resolve().parents[1]
LOCK = json.loads((ROOT/'versions-lock.json').read_text())
WIN = os.name == 'nt'
MODEL = LOCK['model']
CALL_LIMITS = {'latest-linux':10, 'latest-windows':4, 'baseline-linux':4}
SPAWN_LIMITS = {'latest-linux':6, 'latest-windows':3, 'baseline-linux':3}


class InfrastructureError(RuntimeError):
    pass


def executable(args):
    resolved = shutil.which(str(args[0])) or str(args[0])
    args = [resolved, *map(str,args[1:])]
    if WIN and resolved.lower().endswith(('.cmd','.bat')):
        return [os.environ.get('COMSPEC','cmd.exe'), '/d', '/s', '/c', subprocess.list2cmdline(args)]
    return args


def terminate(proc):
    if proc.poll() is not None:
        return
    if WIN:
        subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],capture_output=True)
    else:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()


class Controller:
    def __init__(self, lane, call_limit=None, spawn_limit=None):
        self.lane = lane
        self.runtime = ROOT/'.runtime'/lane
        self.evidence = ROOT/'evidence'/lane
        self.evidence.mkdir(parents=True, exist_ok=True)
        self.runtime.mkdir(parents=True, exist_ok=True)
        self.calls = 0
        self.call_limit=call_limit or CALL_LIMITS[lane]
        self.spawn_limit=spawn_limit or SPAWN_LIMITS[lane]
        self.spawns = set()
        self.results = []
        self.identities = set()
        self.protected = {str(p):digest(p) for p in [ROOT/'versions-lock.json', *sorted((ROOT/'scripts').glob('*.py'))]}
        self.env = os.environ.copy()
        self.home = self.runtime/'codex'
        self.tmp = self.runtime/'tmp'
        self.home.mkdir(exist_ok=True)
        self.tmp.mkdir(exist_ok=True)
        self.env.update({'CODEX_HOME':str(self.home), 'NO_COLOR':'1', 'PYTHONUTF8':'1',
                         'PYTHONIOENCODING':'utf-8', 'SPECKIT_BRIDGE_ACTOR':'codex',
                         'TMPDIR':str(self.tmp), 'TEMP':str(self.tmp), 'TMP':str(self.tmp)})
        self.env.update({'GIT_CONFIG_COUNT':'2','GIT_CONFIG_KEY_0':'core.autocrlf',
                         'GIT_CONFIG_VALUE_0':'false','GIT_CONFIG_KEY_1':'core.longpaths',
                         'GIT_CONFIG_VALUE_1':'true'})
        # A model gets auth via its private Codex home; no GitHub mutation token.
        for key in list(self.env):
            if (key in {'KRILL_API_KEY','OPENAI_API_KEY','CODEX_API_KEY','GH_TOKEN','GITHUB_TOKEN',
                        'ACTIONS_ID_TOKEN_REQUEST_TOKEN','ACTIONS_RUNTIME_TOKEN'}):
                self.env.pop(key,None)
        if WIN:
            native = Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/Modules'
            self.env['PSModulePath']=str(native)
        self.ready=False
        self.case_deadline=None
        self.save()

    def command(self, name, args, cwd=None, *, check=True, input=None, env=None, timeout=300):
        proc=subprocess.run(executable(args),cwd=cwd or ROOT,env=env or self.env,input=input,
                            text=True,encoding='utf-8',errors='replace',capture_output=True,timeout=timeout)
        write(self.evidence/'setup'/f'{name}.log',redact(proc.stdout+'\n[stderr]\n'+proc.stderr))
        write(self.evidence/'setup'/f'{name}.json',json.dumps({'command':list(map(str,args)),
                'cwd':str(cwd or ROOT),'exit_code':proc.returncode},indent=2))
        print(f'{self.lane}: {name}: exit {proc.returncode}',flush=True)
        if check and proc.returncode:
            raise InfrastructureError(f'{name} exited {proc.returncode}: {redact(proc.stderr[-1500:])}')
        return proc

    def record(self,name,status,detail,**extra):
        self.results.append({'name':name,'status':status,'detail':detail,**extra})
        print(f'{self.lane}: {name}: {status}: {detail}',flush=True)
        self.save()

    def save(self):
        write(self.evidence/'results.json',json.dumps({'lane':self.lane,'model_calls':self.calls,
            'reviewer_spawns':len(self.spawns),'models_observed':sorted(self.identities),
            'scenarios':self.results,'connectivity_ready':self.ready,
            'limits':{'calls':self.call_limit,'reviewers':self.spawn_limit},
            'requested_model':MODEL},indent=2))

    def setup(self,authenticate=True):
        shutil.copytree(ROOT/'config',self.home,dirs_exist_ok=True)
        shutil.copyfile(ROOT/'config/codex-ci.toml',self.home/'config.toml')
        group=LOCK['baseline' if self.lane.startswith('baseline') else 'latest']
        self.sources={}
        for name,repo,tag,sha in [
            ('spec-kit','https://github.com/github/spec-kit.git',group['spec_kit_tag'],group['spec_kit_sha']),
            ('superpowers','https://github.com/obra/superpowers.git',group['superpowers_tag'],group['superpowers_sha'])]:
            dest=self.runtime/name
            if not dest.exists():
                self.command('clone-'+name,['git','-c','core.autocrlf=false','clone','--depth','1','--branch',tag,repo,dest],timeout=300)
            head=self.command('head-'+name,['git','rev-parse','HEAD'],dest).stdout.strip()
            if head != sha:
                raise InfrastructureError(f'{name} tag SHA mismatch: {head}')
            self.sources[name]=dest
        venv=self.runtime/'specify-venv'
        vpython=venv/('Scripts/python.exe' if WIN else 'bin/python')
        if not vpython.exists():
            self.command('venv',['uv','venv','--python',sys.executable,venv])
        self.command('install-spec-kit',['uv','pip','install','--python',vpython,str(self.sources['spec-kit'])],timeout=600)
        self.specify=str(venv/('Scripts/specify.exe' if WIN else 'bin/specify'))
        self.command('spec-kit-version',[self.specify,'version'])
        version=self.command('codex-version',['codex','--version']).stdout.strip()
        if LOCK['codex'] not in version:
            raise InfrastructureError(f'Codex version mismatch: {version}')
        archive=self.runtime/'bridge-v1.3.0.zip'
        if not archive.exists():
            urllib.request.urlretrieve(LOCK['bridge']['asset'],archive)
        if digest(archive) != LOCK['bridge']['asset_sha256']:
            raise InfrastructureError('Bridge release ZIP SHA256 mismatch')
        # Install via the native Codex plugin marketplace from the pinned checkout.
        marketplace=self.sources['superpowers']/'.agents/plugins/marketplace.json'
        if not marketplace.exists():
            raise InfrastructureError('Pinned SP release has no native Codex marketplace manifest')
        market=json.loads(marketplace.read_text())['name']
        self.command('plugin-marketplace',['codex','plugin','marketplace','add',self.sources['superpowers'],'--json'])
        self.command('plugin-install',['codex','plugin','add',f'superpowers@{market}','--json'])
        self.command('plugin-list',['codex','plugin','list','--json'])
        self.plugin_files={}
        for path in (self.home/'plugins').rglob('SKILL.md'):
            if path.parent.name in {'executing-plans','test-driven-development','requesting-code-review',
                                    'verification-before-completion','finishing-a-development-branch'}:
                self.plugin_files[str(path.relative_to(self.home))]=digest(path)
        if not any('executing-plans' in p for p in self.plugin_files):
            raise InfrastructureError('Native plugin install did not expose executing-plans')
        # Compare installed native skill bytes against the pinned upstream checkout.
        for relative,sha in self.plugin_files.items():
            skill=Path(relative).parent.name
            if sha != digest(self.sources['superpowers']/'skills'/skill/'SKILL.md'):
                raise InfrastructureError('Installed SP skill differs from pinned upstream: '+skill)
        write(self.evidence/'versions.json',json.dumps({'locked':LOCK,'lane_versions':group,
              'codex_version':version,'plugin_skill_hashes':self.plugin_files,
              'bridge_zip_sha256':digest(archive)},indent=2))
        if authenticate:
            key=os.environ.get('KRILL_API_KEY','')
            if not key:
                raise InfrastructureError('KRILL_API_KEY is missing')
            self.command('codex-login',['codex','login','--with-api-key'],input=key+'\n')
        self.archive=archive

    def prepare(self,name,kind=None):
        root=self.runtime/'projects'/name
        root.mkdir(parents=True)
        flavor='ps' if WIN else 'sh'
        self.command(name+'-init',[self.specify,'init','--here','--force','--non-interactive',
                    '--integration','codex','--script',flavor,'--ignore-agent-tools'],root)
        self.command(name+'-bridge',[self.specify,'extension','add','speckit-superpowers-bridge',
                    '--from',LOCK['bridge']['asset']],root,input='y\n')
        skill_names=sorted(p.parent.name for p in (root/'.agents/skills').glob('*/SKILL.md'))
        expected={'speckit-superpowers-bridge','speckit-speckit-superpowers-bridge-execute',
                  'speckit-speckit-superpowers-bridge-handoff','speckit-speckit-superpowers-bridge-guard',
                  'speckit-specify','speckit-plan','speckit-tasks','speckit-analyze'}
        missing=expected-set(skill_names)
        if missing:
            raise InfrastructureError('Missing installed skills: '+str(sorted(missing)))
        extension=root/'.specify/extensions/speckit-superpowers-bridge'
        # Verify installed release files against the published ZIP where present.
        with zipfile.ZipFile(self.archive) as z:
            entries=z.namelist()
            manifest=next(n for n in entries if n.endswith('extension.yml'))
            prefix=manifest[:-len('extension.yml')]
            hashes={}
            for entry in entries:
                if entry.endswith('/') or not entry.startswith(prefix):
                    continue
                relative=entry[len(prefix):]
                path=extension/relative
                if path.exists() and path.is_file():
                    # On Windows, checkout conversion is not involved in ZIP install.
                    if path.read_bytes() != z.read(entry):
                        raise InfrastructureError('Bridge installed bytes changed: '+relative)
                    hashes[relative]=digest(path)
        write(self.evidence/name/'installation.json',json.dumps({'skills':skill_names,
              'bridge_file_hashes':hashes,'script':flavor},indent=2))
        write(root/'.gitignore','.superpowers/\n__pycache__/\n.pytest_cache/\n*.pyc\n.worktrees/\n')
        if kind:
            create(root,kind)
        # Harness behavioral limits are explicit approved answers, not upstream patches.
        write(root/'CI_CONSTRAINTS.md',f'''# Approved test session answers
Only gpt-6.1-sol is permitted for every model and reviewer. Select it explicitly
when spawning; at most one reviewer in this invocation, no implementer subagents.
If the branch finishing skill presents options, the approved answer is option 3:
keep this branch. No merge, push, publish or discard. This directory is already
an isolated disposable feature checkout; use the existing directory and branch.
Use pytest for model-written tests. All product scope is approved. Implement the
canonical artifacts without adding requirements. Genuine requirement gaps return
to the design owner through Bridge's error handling. Do not alter the CI runner
or evidence outside this consumer checkout. Temp adapters may be written under
the configured TMPDIR/TEMP directory; preserve native skill behavior.
''')
        self.command(name+'-git-init',['git','init','-b','main'],root)
        self.command(name+'-git-name',['git','config','user.name','Compatibility Fixture'],root)
        self.command(name+'-git-email',['git','config','user.email','fixture@example.invalid'],root)
        self.command(name+'-git-add',['git','add','.'],root)
        self.command(name+'-git-commit',['git','commit','-m','test: fixed consumer inputs'],root)
        self.command(name+'-git-branch',['git','switch','-c','feature/'+name],root)
        return root

    def read_artifacts(self,root):
        answer={}
        for path in [root/'.specify/memory/constitution.md',*sorted((root/'specs').glob('*/*.md'))]:
            if path.exists():
                answer[str(path.relative_to(root))]=path.read_text(encoding='utf-8-sig')
        return answer

    def state(self,root):
        path=root/'.specify/superpowers-handoff.json'
        return json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else {}

    def snapshot(self,name,root):
        destination=self.evidence/name/'snapshot'
        for path in root.rglob('*'):
            if not path.is_file() or any(part in {'.git','__pycache__','.pytest_cache','.worktrees'} for part in path.relative_to(root).parts):
                continue
            if path.suffix.lower() in {'.md','.py','.json','.jsonl','.yml','.yaml','.toml','.txt','.sh','.ps1'} or path.name in {'.gitignore','FAIL_POST'}:
                target=destination/path.relative_to(root)
                target.parent.mkdir(parents=True,exist_ok=True)
                if path.stat().st_size < 5000000:
                    target.write_text(redact(path.read_text(encoding='utf-8-sig',errors='replace')),encoding='utf-8')
        self.command(name+'-git-log',['git','log','--format=%H %s','--all'],root,check=False)
        has_main=self.command(name+'-main-ref',['git','rev-parse','--verify','main'],root,check=False).returncode==0
        self.command(name+'-git-diff',['git','diff',*(['main'] if has_main else []),'--'],root,check=False)
        self.command(name+'-git-status',['git','status','--porcelain'],root,check=False)
        self.command(name+'-git-remotes',['git','remote','-v'],root,check=False)

    def capture_scratch(self,root,destination,seen):
        for base in [root/'.superpowers',self.tmp]:
            for path in base.rglob('*.md'):
                try:
                    data=path.read_bytes()
                    if len(data)>5000000:
                        continue
                    sha=hashlib.sha256(data).hexdigest()
                    token=(str(path),sha)
                    if token in seen:
                        continue
                    seen.add(token)
                    label=hashlib.sha256(str(path).encode()).hexdigest()[:12]+'-'+sha[:12]+'.md'
                    write(destination/'scratch'/label,redact(data.decode('utf-8',errors='replace')))
                    with (destination/'scratch-index.jsonl').open('a',encoding='utf-8') as stream:
                        stream.write(json.dumps({'source':str(path),'sha256':sha,'file':'scratch/'+label})+'\n')
                except (OSError,UnicodeError):
                    pass

    def scan_sessions(self):
        for path in (self.home/'sessions').rglob('*.jsonl'):
            try:
                for line in path.read_text(encoding='utf-8',errors='replace').splitlines():
                    try:
                        row=json.loads(line)
                    except ValueError:
                        continue
                    payload=row.get('payload',{})
                    if row.get('type')=='turn_context' and payload.get('model'):
                        self.identities.add(payload['model'])
                    if row.get('type')=='response_item' and payload.get('type')=='function_call' and re.search(r'(?:^|[._])spawn_agent$',payload.get('name','')):
                        self.spawns.add(payload.get('call_id') or hashlib.sha256(line.encode()).hexdigest())
                        try:
                            arguments=json.loads(payload.get('arguments','{}'))
                        except ValueError:
                            arguments={}
                        if arguments.get('model') and arguments['model'] != MODEL:
                            raise InfrastructureError('Model boundary violated in reviewer spawn: '+arguments['model'])
            except OSError:
                pass
        if self.identities-{MODEL}:
            raise InfrastructureError('Unexpected session model: '+str(self.identities-{MODEL}))
        if len(self.spawns)>self.spawn_limit:
            raise InfrastructureError('Reviewer spawn budget exceeded')

    def call(self,name,root,prompt,effort='xhigh',interrupt=False,time_budget_seconds=None,
             *, interrupt_check=None, max_reviewers=1, finish_choice='keep'):
        if self.calls >= self.call_limit:
            raise InfrastructureError('Top-level Codex invocation budget exhausted')
        if self.case_deadline and time.monotonic() >= self.case_deadline:
            raise InfrastructureError('Scenario exceeded approved 40-minute limit')
        self.calls+=1
        destination=self.evidence/name
        destination.mkdir(parents=True,exist_ok=True)
        suffix=(f'\nOnly model gpt-6.1-sol is allowed, including reviewers. '
                f'At most {max_reviewers} reviewer spawn(s) in this invocation.')
        if finish_choice=='keep':
            suffix+=' Finish choice is keep branch (option 3).'
        else:
            suffix+=' Follow only the explicitly authorized finishing choices in the scenario.'
        prompt='Read CI_CONSTRAINTS.md first if present. '+prompt+suffix
        write(destination/'prompt.txt',prompt)
        args=['codex','--no-daemon','exec','--json','--color','never','-m',MODEL,
              '-c',f"model_reasoning_effort='{effort}'",'-c',"model_provider='krill'",
              '--dangerously-bypass-approvals-and-sandbox','-C',root,
              '--output-last-message',destination/'last-message.md','-']
        write(destination/'invocation.json',json.dumps({'command':list(map(str,args)),
              'model':MODEL,'reasoning':effort,'provider':'krill'},indent=2))
        print(f'{self.lane}: real model call {self.calls}/{self.call_limit}: {name}',flush=True)
        self.save()
        started=time.monotonic()
        interrupted=False
        reason=None
        seen=set()
        with (destination/'events.jsonl').open('w',encoding='utf-8') as out, (destination/'stderr.log').open('w',encoding='utf-8') as err:
            proc=subprocess.Popen(executable(args),cwd=root,env=self.env,stdin=subprocess.PIPE,
                                  stdout=out,stderr=err,text=True,encoding='utf-8',
                                  start_new_session=not WIN,
                                  creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if WIN else 0)
            proc.stdin.write(prompt)
            proc.stdin.close()
            try:
                while proc.poll() is None:
                    self.capture_scratch(root,destination,seen)
                    self.scan_sessions()
                    for path,sha in self.protected.items():
                        if digest(path)!=sha:
                            raise InfrastructureError('External controller/verifier integrity changed')
                    if interrupt_check is not None and interrupt_check():
                        interrupted=True
                        reason='Terminated externally after committed canonical T001 completed'
                        terminate(proc)
                        break
                    if interrupt:
                        checked=[p for p in (root/'specs').glob('*/tasks.md') if any(t[0]=='T001' and t[1] for t in tasks(p))]
                        if checked:
                            interrupted=True
                            reason='Terminated externally immediately after canonical T001 completed'
                            terminate(proc)
                            break
                    if (time.monotonic()-started>(time_budget_seconds or LOCK['limits']['call_timeout_seconds']) or
                        (self.case_deadline and time.monotonic()>self.case_deadline)):
                        reason='Codex invocation/scenario exceeded approved timeout'
                        terminate(proc)
                        break
                    time.sleep(0.3)
            except BaseException:
                terminate(proc)
                raise
        self.capture_scratch(root,destination,seen)
        self.scan_sessions()
        result={'exit_code':proc.returncode,'seconds':round(time.monotonic()-started,2),
                'interrupted':interrupted,'termination_reason':reason}
        events=(destination/'events.jsonl').read_text(encoding='utf-8',errors='replace')
        errors=(destination/'stderr.log').read_text(encoding='utf-8',errors='replace')
        result['flags']=evidence_flags(events)
        result['usage']=[]
        for line in events.splitlines():
            try:
                row=json.loads(line)
                if row.get('type')=='turn.completed':
                    result['usage'].append(row.get('usage',{}))
            except ValueError:
                pass
        write(destination/'process.json',json.dumps(result,indent=2))
        self.snapshot(name,root)
        self.save()
        # Stop, rather than switch provider/model, on definitive service failures.
        if re.search(r'401 Unauthorized|403 Forbidden|invalid[_ ]api[_ ]key|model.{0,50}(?:not found|not available|does not exist)|insufficient_quota',events+'\n'+errors,re.I):
            raise InfrastructureError('Authentication/model availability failure; see '+name+'/events.jsonl')
        return result

    def probe(self):
        root=self.runtime/'probe'
        root.mkdir(exist_ok=True)
        self.command('probe-git',['git','init','-b','probe'],root)
        prompt='Use a shell tool to create connection-probe.txt with exactly KRILL-CODEX-TOOLS-OK, then use a shell tool to read it. Do not use any project development skill or spawn a reviewer.'
        attempt=self.call('connection-probe',root,prompt,'low')
        path=root/'connection-probe.txt'
        passed=path.exists() and path.read_text().strip()=='KRILL-CODEX-TOOLS-OK' and attempt['flags']['command_count']>=2 and attempt['exit_code']==0
        if not passed:
            err=(self.evidence/'connection-probe'/'stderr.log').read_text(errors='replace')
            events=(self.evidence/'connection-probe'/'events.jsonl').read_text(errors='replace')
            if self.lane=='latest-linux' and re.search(r'502|503|504|connection reset|stream disconnected|timed out',err+events,re.I):
                attempt=self.call('connection-probe-retry',root,prompt,'low')
                passed=path.exists() and path.read_text().strip()=='KRILL-CODEX-TOOLS-OK' and attempt['flags']['command_count']>=2 and attempt['exit_code']==0
        self.ready=passed
        self.record('connection and shell tools','pass' if passed else 'blocked',
                    'Responses and two real shell operations observed' if passed else 'No successful two-operation tool round trip; no compatibility inference')
        if not passed:
            raise InfrastructureError('Connection/tool probe failed; stop live calls')

    def handoff_valid(self,root):
        state=self.state(root)
        feature=state.get('feature_directory','')
        return bool(feature and all((root/feature/name).exists() for name in ['spec.md','plan.md','tasks.md'])
                    and state.get('status') in {'ready','executing'})

    def execute_prompt(self):
        return '$speckit-superpowers-bridge\nUse the installed bridge skill on the active canonical Spec Kit feature. Execute the full lifecycle through native Superpowers skills. All implementation is authorized. Follow CI_CONSTRAINTS.md. Do not patch installed skills. At finishing, the preapproved answer is keep this branch.'

    def main_case(self,generated):
        self.case_deadline=time.monotonic()+2400
        root=self.prepare('main',None if generated else 'main')
        if generated:
            self.call('sk-specification',root,
                '$speckit-constitution\nUse the installed constitution skill to establish these principles:\n'+CONSTITUTION+
                '\nThen use $speckit-specify to create the approved feature from:\n'+PRODUCT+
                '\nUse $speckit-clarify if needed; the requirements above are the approved answers. Stop after specification; do not plan or implement.','high')
            self.call('sk-plan',root,'$speckit-plan\nUse the installed SK plan skill for the active feature. Implement with Python standard library and pytest. Aim for three cohesive implementation tasks: repository, domain operations, CLI. Stop after planning, do not implement.','high')
            result=self.call('sk-tasks-analyze',root,
                '$speckit-tasks\nUse the installed task-generation skill for the active feature, targeting three cohesive tasks where consistent with SK. Honor automatic mandatory hooks. Then use $speckit-analyze for a read-only consistency review. Stop before implementation.','high')
            valid=self.handoff_valid(root)
            self.record('SK generation and automatic after_tasks handoff','pass' if valid else 'fail',
                        'Real SK-generated artifacts and active bridge handoff exist' if valid else 'SK artifacts or automatic bridge handoff missing')
        else:
            result=self.call('fixture-handoff',root,
                '$speckit-speckit-superpowers-bridge-handoff\nUse the installed canonical handoff command for the active fixed fixture. Also run the installed bridge readiness check using the selected platform script. Stop before implementation.','high')
            valid=self.handoff_valid(root)
            self.record('fixture handoff and installed entry discovery','pass' if valid else 'fail',
                        'Canonical entry created active handoff; alias present in installed skill registry' if valid else 'Fixed artifacts could not be handed off')
        if not valid:
            self.record('complete product lifecycle','blocked','Cannot execute without a valid handoff; original failure retained')
            return root,False
        before=self.read_artifacts(root)
        execution_base=self.command('execution-base',['git','rev-parse','HEAD'],root).stdout.strip()
        execution=self.call('bridge-execute',root,self.execute_prompt())
        acceptance=product(root)
        write(self.evidence/'bridge-execute'/'external-acceptance.json',json.dumps(acceptance,indent=2))
        state=self.state(root)
        feature=state.get('feature_directory','')
        items=tasks(root/feature/'tasks.md') if feature and (root/feature/'tasks.md').exists() else []
        preserved=immutable_artifacts(before,self.read_artifacts(root))
        commit_count=int(self.command('execution-commit-count',['git','rev-list','--count',execution_base+'..HEAD'],root).stdout.strip())
        branch=self.command('execution-branch',['git','branch','--show-current'],root).stdout.strip()
        remotes=self.command('execution-remotes',['git','remote','-v'],root).stdout.strip()
        checks={'black_box':acceptance['pass'],'handoff_complete':state.get('status')=='complete',
                'all_tasks_checked':bool(items) and all(t[1] for t in items),
                'canonical_requirements_preserved':all(preserved.values()),
                'real_bridge_update':execution['flags']['bridge_update'],
                'real_native_execution_read':execution['flags']['native_executor_read'],
                'commits_per_task':commit_count>=len(items),
                'kept_feature_branch':branch not in {'','main','master'} and not remotes}
        self.record('complete product lifecycle','pass' if all(checks.values()) else 'fail',
                    json.dumps(checks),checks=checks,external_acceptance=acceptance)
        flags=execution['flags']
        discipline={key:flags[key] for key in ['tdd_read','verification_read','review_read','finish_read','red','green']}
        self.record('native TDD verification review and finishing','pass' if all(discipline.values()) else 'fail',json.dumps(discipline),checks=discipline)
        scratch=[]
        for p in (self.evidence/'bridge-execute'/'scratch').glob('*.md'):
            text=p.read_text()
            if re.search(r'^### Task \d+: T\d+',text,re.M):
                scratch.append(text)
        mapping=bool(scratch) and all(any(t[0] in text and t[2] in text for text in scratch) for t in items)
        self.record('disposable Task N adapter mapping','pass' if mapping else 'blocked',
                    'Exact canonical task IDs and text observed in temporary adapters' if mapping else 'Full exact adapter mapping evidence unavailable')
        self.record('canonical progress and drift', 'pass' if all(preserved.values()) else 'fail',
                    'Requirements preserved; legal checkbox progress drift warning: '+str(flags['drift_warning']),preserved=preserved)
        return root,state.get('status')=='complete'

    def second_feature(self,root,complete):
        self.case_deadline=time.monotonic()+2400
        if not complete:
            self.record('next feature and archival','blocked','First handoff is not complete; no fake completion seeded')
            return
        before=self.state(root).get('feature_directory')
        self.call('second-feature',root,
            '$speckit-specify\nBegin a second approved independent feature: python -m task_app --store PATH stats prints JSON with total and completed integer counts and no store mutations. Use the installed SK specify skill; ensure the completed prior bridge lifecycle is handled through its documented archive protocol. Stop after spec generation. No implementation or planning.','high')
        pointer=json.loads((root/'.specify/feature.json').read_text(encoding='utf-8-sig'))
        events=(root/'.specify/bridge-events.jsonl').read_text(errors='replace')
        archived=any(json.loads(line).get('action')=='archive' for line in events.splitlines() if line.strip())
        state=self.state(root)
        passed=pointer.get('feature_directory')!=before and archived and state.get('status')!='complete'
        self.record('next feature and archival','pass' if passed else 'fail',
                    f'new feature pointer: {pointer.get("feature_directory")}; archive event: {archived}; bridge status: {state.get("status")}')

    def synthetic_state(self,root):
        # Public failure fixture setup, not a substitute for model skill execution.
        feature=json.loads((root/'.specify/feature.json').read_text())['feature_directory']
        state={'schema_version':'1.0','feature_directory':feature,'status':'ready',
               'artifact_owner':'codex','actor':'codex','executor':'superpowers',
               'supersedes':['speckit.implement'],'source_of_truth':{
                   'constitution':'.specify/memory/constitution.md','spec':feature+'/spec.md',
                   'plan':feature+'/plan.md','tasks':feature+'/tasks.md'}}
        write(root/'.specify/superpowers-handoff.json',json.dumps(state,indent=2))

    def resume_case(self):
        self.case_deadline=time.monotonic()+2400
        root=self.prepare('resume','resume')
        self.synthetic_state(root)
        first=self.call('resume-interruption',root,self.execute_prompt(),interrupt=True)
        if not first['interrupted']:
            self.record('interruption and fresh-session resume','blocked','Controller never observed canonical T001 completion before process ended')
            return
        first_logs=self.command('resume-before-log',['git','log','--format=%H %s'],root).stdout
        original_function=None
        source=root/'resume_app.py'
        if source.exists():
            import ast
            original_function=next((ast.dump(n) for n in ast.parse(source.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='normalize_title'),None)
        final=self.call('resume-fresh-session',root,self.execute_prompt())
        verification=resume_product(root)
        state=self.state(root)
        items=tasks(root/'specs/001-resume/tasks.md')
        after_function=None
        if source.exists():
            import ast
            after_function=next((ast.dump(n) for n in ast.parse(source.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='normalize_title'),None)
        checks={'interrupted_after_T001':True,'all_canonical_tasks_complete':all(t[1] for t in items),
                'all_three_features_work':verification['pass'],'handoff_complete':state.get('status')=='complete',
                'T001_function_preserved':bool(original_function) and original_function==after_function}
        write(self.evidence/'resume-fresh-session'/'external-acceptance.json',json.dumps(verification,indent=2))
        self.record('interruption and fresh-session resume','pass' if all(checks.values()) else 'fail',json.dumps(checks),checks=checks)

    def hook_case(self):
        self.case_deadline=time.monotonic()+2400
        import yaml
        root=self.prepare('hook-failure','hook')
        self.synthetic_state(root)
        write(root/'ci_hooks/fail_post.py',"from pathlib import Path\nimport json\np=Path('.specify/hook-failure-marker.json')\np.write_text(json.dumps({'executed':True,'exit_code':23}))\nraise SystemExit(23)\n")
        write(root/'.agents/skills/speckit-ci-postcheck/SKILL.md','''---
name: speckit-ci-postcheck
description: Mandatory synthetic CI post implementation hook.
---
# Mandatory post-hook
Run `python ci_hooks/fail_post.py` from repository root and wait for its result.
Report the actual nonzero exit. This fixture intentionally fails; do not repair it.
''')
        registry=root/'.specify/extensions.yml'
        data=yaml.safe_load(registry.read_text())
        data.setdefault('hooks',{}).setdefault('after_implement',[]).append({
            'extension':'ci-fixture','command':'speckit.ci.postcheck','enabled':True,
            'optional':False,'priority':10,'condition':None,'description':'Intentional mandatory post-hook exit 23'})
        write(registry,yaml.safe_dump(data,sort_keys=False))
        self.call('mandatory-posthook-failure',root,self.execute_prompt())
        marker=root/'.specify/hook-failure-marker.json'
        state=self.state(root)
        actual=marker.exists() and json.loads(marker.read_text()).get('executed') is True
        passed=actual and state.get('status')!='complete'
        self.record('mandatory failing post-hook','pass' if passed else 'fail',
                    f'Hook really executed: {actual}; handoff status: {state.get("status")}')

    def conflict_case(self):
        self.case_deadline=time.monotonic()+2400
        root=self.prepare('spec-conflict','conflict')
        self.synthetic_state(root)
        before=self.read_artifacts(root)
        self.call('spec-conflict',root,self.execute_prompt())
        state=self.state(root)
        preserved=immutable_artifacts(before,self.read_artifacts(root))
        stopped=state.get('status')=='blocked' and not (root/'marker.py').exists() and all(preserved.values())
        self.record('spec versus tasks conflict','pass' if stopped else 'fail',
                    f'Blocked: {state.get("status")=="blocked"}; application written: {(root/"marker.py").exists()}; canonical docs preserved: {all(preserved.values())}')

    def boundary_case(self):
        self.case_deadline=time.monotonic()+2400
        root=self.prepare('boundaries','boundary')
        self.synthetic_state(root)
        data=self.state(root)
        data['status']='executing'
        write(root/'.specify/superpowers-handoff.json',json.dumps(data,indent=2))
        before=self.read_artifacts(root)
        self.call('guard-boundaries',root,
            'Compatibility guard test: use the installed bridge guard entry and attempt each prohibited operation through its documented guard: speckit.implement, superpowers:writing-plans, superpowers:brainstorming, and speckit.constitution while executing. Run the actual guard for each operation and obey its decision. This is a boundary test; do not implement an application. Also invoke the installed read-only bridge-status to inspect drift. Stop after decisions.','high')
        events=root/'.specify/bridge-events.jsonl'
        rows=[json.loads(l) for l in events.read_text().splitlines()] if events.exists() else []
        denied={r.get('checked_action') for r in rows if r.get('decision')=='deny'}
        expected={'speckit.implement','superpowers:writing-plans','superpowers:brainstorming','speckit.constitution'}
        intact=all(immutable_artifacts(before,self.read_artifacts(root)).values())
        self.record('prohibited boundaries','pass' if expected<=denied and intact else 'fail',
                    f'Actual guard denies: {sorted(denied)}; canonical docs preserved: {intact}')

    def finish(self):
        self.scan_sessions()
        # Only rollouts are exported, never auth/config databases or environment dumps.
        for path in (self.home/'sessions').rglob('*.jsonl'):
            target=self.evidence/'sessions'/path.relative_to(self.home/'sessions')
            write(target,redact(path.read_text(encoding='utf-8',errors='replace')))
        self.save()
        sanitize(self.evidence)
        if os.environ.get('GITHUB_OUTPUT'):
            with open(os.environ['GITHUB_OUTPUT'],'a') as output:
                output.write('ready='+str(self.ready).lower()+'\n')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--lane',choices=CALL_LIMITS,required=True)
    parser.add_argument('--setup-only',action='store_true')
    args=parser.parse_args()
    controller=Controller(args.lane)
    try:
        controller.setup(authenticate=not args.setup_only)
        if args.setup_only:
            controller.prepare('installation-probe','main')
            controller.record('local setup','pass','No model calls; fixed upstream installation checked')
            return
        if args.lane=='latest-linux':
            previous=json.loads((ROOT/'prior-runs/38245424879-summary.json').read_text())
            if previous.get('probe_succeeded') and previous.get('model')==MODEL:
                controller.ready=True
                controller.record('connection and shell tools','pass','Reused externally checked successful first-run probe; original run and exact usage retained in prior-runs')
            else:
                raise InfrastructureError('Retained probe is not valid')
        else:
            controller.probe()
        root,complete=controller.main_case(generated=args.lane=='latest-linux')
        controller.second_feature(root,complete)
        if args.lane=='latest-linux':
            controller.resume_case()
            controller.hook_case()
            controller.conflict_case()
            controller.boundary_case()
    except InfrastructureError as exc:
        controller.ready=False
        controller.record('infrastructure or approved limit','blocked',str(exc))
    except Exception as exc:
        write(controller.evidence/'controller-error.log',redact(traceback.format_exc()))
        controller.record('controller error','blocked',str(exc))
    finally:
        controller.finish()


if __name__=='__main__':
    main()
