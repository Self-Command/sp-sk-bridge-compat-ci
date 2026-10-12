import json,subprocess,sys
from pathlib import Path
phase=sys.argv[1]
p=Path('.specify/superpowers-handoff.json')
s=json.loads(p.read_text(encoding='utf-8-sig')) if p.exists() else {}
code=0
entry={'phase':phase,'status_before':s.get('status'),'feature':s.get('feature_directory')}
if phase=='pre' and Path('ci_hooks/FAIL_PRE').exists():code=17
if phase=='post':
 p=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],capture_output=True,text=True)
 print(p.stdout+p.stderr)
 entry['suite_exit']=p.returncode
 code=p.returncode
 if Path('ci_hooks/FAIL_POST').exists():code=23
if phase=='sentinel':code=29
entry['exit_code']=code
with Path('.specify/full-hook-events.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(entry)+'\n')
print(json.dumps(entry))
raise SystemExit(code)
