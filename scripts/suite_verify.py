"""Independent evidence checks for the complete small-project workflow."""
import json
import re
from pathlib import Path


def command_records(path):
    records=[]
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        try:
            event=json.loads(line)
        except ValueError:
            continue
        item=event.get('item',{})
        if event.get('type')=='item.completed' and item.get('type')=='command_execution':
            records.append(item)
    return records


def tdd_order(records):
    """An empty test run or skill-file read cannot prove red or green."""
    red=[]; green=[]
    for index,item in enumerate(records):
        output=item.get('aggregated_output','')
        if not re.search(r'python\S*\s+.*(?:unittest|pytest)',item.get('command','')):
            continue
        if item.get('exit_code') not in {0,None} and re.search(r'FAILED \((?:failures|errors)=|\d+ failed',output):
            red.append(index)
        if re.search(r'Ran [1-9]\d* tests?\b[\s\S]*\bOK\b|\d+ passed',output):
            green.append(index)
    return bool(red and green and min(red)<max(green))


def injected_skills(directory):
    """Read runtime-injected skill messages, never assistant success prose."""
    found=set()
    for path in Path(directory).rglob('*.jsonl'):
        for line in path.read_text(encoding='utf-8',errors='replace').splitlines():
            try:
                event=json.loads(line)
            except ValueError:
                continue
            payload=event.get('payload',{})
            if event.get('type')=='response_item' and payload.get('type')=='message' and payload.get('role')=='user':
                body=''.join(p.get('text','') for p in payload.get('content',[]))
                found.update(re.findall(r'<skill>\s*<name>([^<]+)</name>',body))
    return found


def rows(path):
    path=Path(path)
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()] if path.exists() else []


def preserved_contracts(before,after):
    """Allow evidence explicitly required by the original task; never allow requirement edits."""
    def normalize(text):
        text=re.sub(r'^(- \[)[xX](\] T\d+)',r'\1 \2',text,flags=re.M)
        # Native generated task prose describes execution progress separately
        # from requirements. Permit this exact pending -> evidence status change.
        return text.replace('Implementation remains pending.','Implementation [progress].').replace('Implementation evidence follows.','Implementation [progress].')
    checks={}
    for name,old in before.items():
        new=after.get(name,'')
        left=normalize(old);right=normalize(new)
        if left==right:
            checks[name]=True
            continue
        appendix=right[len(left):] if right.startswith(left) else ''
        original_lines=re.findall(r'^- \[[ xX]\] T\d+.*$',old,re.M)
        evidence_requested=any('tasks.md' in line and re.search(r'evidence|record.*(?:red/green|test|commands|results)',line,re.I) for line in original_lines)
        headings=re.findall(r'^## ([^\n]+)',appendix,re.M)
        # Native SK may explicitly require execution evidence in tasks.md. It must
        # be append-only, with no new task IDs and only execution-evidence headings.
        legal=(name.endswith('/tasks.md') and evidence_requested and bool(appendix.strip())
               and bool(headings) and all(re.fullmatch(r'T\d+ execution evidence',h) for h in headings)
               and not re.search(r'^- \[[ xX]\] T\d+',appendix,re.M))
        checks[name]=legal
    return checks
