"""External black-box checks. This file is never copied into model worktrees."""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tasks(path):
    return [(m.group(2), m.group(1).lower() == 'x', m.group(3)) for m in
            re.finditer(r'^- \[([ xX])\] (T\d+)\s+(.*)$', Path(path).read_text(), re.M)]


def product(root):
    findings = []
    with tempfile.TemporaryDirectory(prefix='external-acceptance-') as directory:
        store = Path(directory)/'tasks.json'

        def cli(*args, code=0, decode=True):
            proc = subprocess.run([sys.executable, '-m', 'task_app', '--store', str(store), *args],
                                  cwd=root, capture_output=True, text=True, timeout=20)
            assert proc.returncode == code, (args, proc.returncode, proc.stdout, proc.stderr)
            return json.loads(proc.stdout) if decode else proc

        try:
            assert cli('list') == []
            findings.append('empty list')
            first = cli('add', '  Alpha  ')
            assert first['title'] == 'Alpha' and first['completed'] is False
            assert type(first['id']) is int and first['id'] > 0
            second = cli('add', '😀'*100)
            assert second['id'] > first['id']
            assert len(cli('list')) == 2
            data = json.loads(store.read_text())
            assert data['version'] == 1 and len(data['tasks']) == 2
            findings.append('trim, Unicode boundary, monotonic IDs, persistence')
            prior = store.read_bytes()
            for invalid in ['', '   ', '😀'*101]:
                cli('add', invalid, code=2, decode=False)
                assert store.read_bytes() == prior
            findings.append('invalid titles rejected without mutation')
            completed = cli('complete', str(first['id']))
            assert completed['completed'] is True
            assert cli('complete', str(first['id']))['completed'] is True
            assert next(t for t in cli('list') if t['id'] == first['id'])['completed'] is True
            findings.append('complete and repeated complete')
            for operation in ['complete', 'delete']:
                prior = store.read_bytes()
                cli(operation, '999999', code=2, decode=False)
                assert store.read_bytes() == prior
            cli('delete', str(first['id']), decode=False)
            assert [t['id'] for t in cli('list')] == [second['id']]
            third = cli('add', 'Third')
            assert third['id'] > second['id']
            cli('delete',str(third['id']),decode=False)
            fourth=cli('add','Fourth')
            assert fourth['id']>third['id']
            findings.append('missing IDs, deletion and no ID reuse')
            for corrupt in ['{broken', '{"version":999,"tasks":[]}',
                            '{"version":1,"tasks":[{"id":1}]}']:
                store.write_text(corrupt)
                for operation in [('list',), ('add', 'New'), ('complete', '1'), ('delete', '1')]:
                    cli(*operation, code=2, decode=False)
                    assert store.read_text() == corrupt
            findings.append('malformed JSON, unsupported version and invalid records preserved')
            return {'pass': True, 'checks': findings}
        except (AssertionError, KeyError, ValueError, subprocess.TimeoutExpired) as exc:
            return {'pass': False, 'checks': findings, 'error': str(exc)}


def resume_product(root):
    script = "import resume_app as a; assert a.normalize_title(' X ')=='X'; assert a.make_task(' Y ')=={'title':'Y','completed':False}"
    proc = subprocess.run([sys.executable, '-c', script], cwd=root, capture_output=True, text=True, timeout=20)
    cli = subprocess.run([sys.executable, 'resume_app.py', ' Z '], cwd=root, capture_output=True, text=True, timeout=20)
    try:
        ok = proc.returncode == cli.returncode == 0 and json.loads(cli.stdout) == {'title':'Z','completed':False}
    except ValueError:
        ok = False
    return {'pass': ok, 'library_exit': proc.returncode, 'cli_exit': cli.returncode,
            'error': proc.stderr+cli.stderr}


def immutable_artifacts(before, after):
    """Checkbox changes are legal progress. Other canonical edits are drift."""
    normalize = lambda t: re.sub(r'^(- \[)[xX](\] T\d+)', r'\1 \2', t, flags=re.M)
    return {name: normalize(text) == normalize(after.get(name, '')) for name, text in before.items()}


def evidence_flags(text):
    """Require tool command records, never count an assistant's success claim."""
    commands = []
    for line in text.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        item = event.get('item', {})
        if item.get('type') == 'command_execution':
            commands.append(item)
    joined = '\n'.join(i.get('command', '') for i in commands)
    output = '\n'.join(str(i.get('aggregated_output', '')) for i in commands)
    tests = [i for i in commands if re.search(r'pytest|unittest|test[_-].*\.py', i.get('command',''))]
    return {'command_count': len(commands), 'commands': joined,
            'bridge_update': 'update-handoff' in joined,
            'native_executor_read': 'executing-plans' in joined and 'SKILL.md' in joined,
            'tdd_read': 'test-driven-development' in joined,
            'verification_read': 'verification-before-completion' in joined,
            'review_read': 'requesting-code-review' in joined,
            'finish_read': 'finishing-a-development-branch' in joined,
            'red': any(i.get('exit_code', 0) != 0 for i in tests),
            'green': any(i.get('exit_code') == 0 for i in tests),
            'drift_warning': 'artifact drift' in output.lower()}
