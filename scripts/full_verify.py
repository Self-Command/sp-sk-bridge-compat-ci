"""Independent checks for the original-release, bounded full bridge suite."""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from suite_verify import command_records, preserved_contracts
from verify import tasks


CONTRACT = '''Build a tiny Python 3.13 standard-library title-to-task JSON tool.
Library in resume_app.py:
normalize_title(title) strips surrounding whitespace and raises ValueError for
empty or whitespace-only strings. Non-empty Unicode titles are accepted.
make_task(title) returns exactly {"title": normalized_title, "completed": false}.
CLI: python resume_app.py TITLE prints that task as JSON and exits 0.
Empty/whitespace-only TITLE or a missing TITLE exits 2. No UI, database,
network, installation, persistence, additional features or runtime dependencies.
Use standard-library unittest and observed TDD. Exactly three ordered cohesive
implementation tasks: T001 normalize_title and its tests, T002 make_task and its
tests depending on T001, T003 the CLI and its tests depending on T001/T002.
Commit each task with its canonical checkbox and actual execution evidence.
The design, these requirements, and all testing answers are authorized by the
user's full compatibility-test plan. Keep documents concise.
'''


def run(root, args, timeout=30):
    p=subprocess.run([sys.executable,*args],cwd=root,capture_output=True,text=True,
                     encoding='utf-8',errors='replace',timeout=timeout)
    return {'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr}


def product(root):
    code='''import resume_app as a
for title,want in [(' X ','X'),('  中文😀  ','中文😀'),('Y','Y')]:
 assert a.normalize_title(title)==want
 assert a.make_task(title)=={'title':want,'completed':False}
for title in ['', '   ', '\\t\\n']:
 for f in [a.normalize_title,a.make_task]:
  try: f(title)
  except ValueError: pass
  else: raise AssertionError('empty title must raise ValueError')
'''
    library=run(root,['-c',code])
    valid=run(root,['resume_app.py',' 中文😀 '])
    invalid=[run(root,['resume_app.py',s]) for s in ['', '  ', '\t\n']]
    missing=run(root,['resume_app.py'])
    try:
        correct=json.loads(valid['stdout'])=={'title':'中文😀','completed':False}
    except ValueError:
        correct=False
    checks={'library_behaviors':library['exit_code']==0,
            'cli_json':valid['exit_code']==0 and correct,
            'invalid_cli_exit_2':all(x['exit_code']==2 for x in invalid),
            'missing_cli_exit_2':missing['exit_code']==2}
    return {'pass':all(checks.values()),'checks':checks,
            'library':library,'valid':valid,'invalid':invalid,'missing':missing}


def tests_pass(result):
    text=result['stdout']+result['stderr']
    return result['exit_code']==0 and bool(re.search(r'Ran [1-9]\d* tests?\b[\s\S]*\bOK\b',text))


def skill_read(records, name):
    return any(x.get('exit_code')==0 and name in x.get('command','')
               and 'SKILL.md' in x.get('command','')
               and re.search(r'\bcat\b|Get-Content|read_text',x.get('command',''))
               for x in records)


def records(root, name):
    p=Path(root)/name/'events.jsonl'
    return command_records(p) if p.exists() else []


def ast_function(path, name):
    for node in ast.walk(ast.parse(Path(path).read_text(encoding='utf-8-sig'))):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name==name:
            return ast.dump(node,include_attributes=False)
    return None


def task_adapter_check(directory, canonical, expected_ids):
    adapters=[]
    for p in Path(directory).glob('scratch/*.md'):
        text=p.read_text(encoding='utf-8')
        if re.search(r'^### Task \d+: T\d+',text,re.M):
            adapters.append(text)
    matched={task_id:any(re.search(r'^### Task \d+: '+re.escape(task_id)+r'\b',a,re.M)
                           and any(line in a for line in canonical.splitlines()
                                   if re.match(r'- \[[ xX]\] '+re.escape(task_id)+r'\b',line))
                        for a in adapters)
             for task_id in expected_ids}
    # Compare against the original unchecked line, not a post-execution checkbox.
    return bool(adapters) and all(matched.values()),matched


def usage(directory):
    totals={'input_tokens':0,'cached_input_tokens':0,'output_tokens':0}
    sessions={}
    for p in Path(directory).rglob('*.jsonl'):
        if not p.name.startswith('rollout-'):
            continue
        last=None;identity=p.name
        for line in p.read_text(encoding='utf-8',errors='replace').splitlines():
            try:e=json.loads(line)
            except ValueError:continue
            d=e.get('payload',{})
            if e.get('type')=='session_meta':identity=d.get('id') or identity
            info=d.get('info') or {}
            if e.get('type')=='event_msg' and d.get('type')=='token_count' and info.get('total_token_usage'):
                last=info['total_token_usage']
        if last and identity not in sessions:sessions[identity]=last
    for last in sessions.values():
        for k in totals:totals[k]+=last.get(k,0)
    totals['non_cached_input_tokens']=totals['input_tokens']-totals['cached_input_tokens']
    return {**totals,'session_count':len(sessions)}


def model_metadata(directory):
    models=set();efforts=set();spawns=[]
    for p in Path(directory).rglob('rollout-*.jsonl'):
        for line in p.read_text(encoding='utf-8',errors='replace').splitlines():
            try:e=json.loads(line)
            except ValueError:continue
            d=e.get('payload',{})
            if e.get('type')=='turn_context':
                if d.get('model'):models.add(d['model'])
                if d.get('effort'):efforts.add(d['effort'])
            if e.get('type')=='response_item' and d.get('type')=='function_call' and 'spawn_agent' in d.get('name',''):
                try:args=json.loads(d.get('arguments','{}'))
                except ValueError:continue
                spawns.append({k:args.get(k) for k in ['model','reasoning_effort','fork_turns','task_name']})
    return {'models':sorted(models),'reasoning':sorted(efforts),'spawns':spawns}


def protected_hashes(root):
    result={}
    for base in [Path(root)/'.agents/skills',Path(root)/'.specify/extensions/speckit-superpowers-bridge']:
        for p in base.rglob('*'):
            if p.is_file():
                result[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest()
    return result


def protected_ok(root, before):
    return all((Path(root)/rel).is_file() and
               hashlib.sha256((Path(root)/rel).read_bytes()).hexdigest()==sha
               for rel,sha in before.items())


def contract_ok(before, after):
    return all(preserved_contracts(before,after).values())
