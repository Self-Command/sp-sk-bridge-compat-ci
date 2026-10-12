"""Report the actual candidate coverage while retaining the original audit mapping."""
from pathlib import Path
import json
import sys
from full_report import main as aggregate
from fixtures import write
from run_full_suite import COMMON_EXPECTED, LINUX_EXPECTED
from run_candidate_suite import CONVERGE_SCENARIOS

root=Path(sys.argv[1])
exit_code=aggregate(root)
data=json.loads((root/'full-results.json').read_text())
data['versions']['bridge']='1.4.0'
data['native_converge_limitation']='Original SK implement prerequisite remains; the separately named bridge converge entry is the supported SP workflow.'
required=[]
for platform in data['platforms']:
    candidate_path=root/platform['lane']/'candidate-coverage.json'
    if candidate_path.exists():
        index=json.loads(candidate_path.read_text())['source']
        required.append(index)
data['candidate_indexes']=required
data['same_candidate']=bool(len(required)==2 and required[0]==required[1])
if not data['same_candidate']:exit_code=1
data['required_coverage_ok']=True
for platform in data['platforms']:
    expected=COMMON_EXPECTED + CONVERGE_SCENARIOS + ([] if platform['lane']=='latest-windows' else LINUX_EXPECTED)
    actual={row['name']:row['status'] for row in platform['scenarios']}
    if any(actual.get(name)!='pass' for name in expected):
        data['required_coverage_ok']=False
if not data['required_coverage_ok']:exit_code=1
write(root/'candidate-results.json',json.dumps(data,ensure_ascii=False,indent=2))
text='\n'.join(['# Bridge v1.4.0 修复版完整回归','',
    '**固定组合**：SK 1.1.3 / SP 7.0.0 / Codex CLI 0.162.1；gpt-6.1-sol、low。',
    f'新增主调用 {data["model_calls"]}/20，审查 {data["reviewer_spawns"]}/6；预算检查 {data["budget_ok"]}。',
    f'结果 {data["counts"]}；两平台候选一致 {data["same_candidate"]}。','',
    '原报告 44 项保留对应场景；缺文档仍要求 blocked。SP 收敛按授权新增桥接入口验收，原生 SK implement 前置要求仍保留。','',
    '| 平台 | 场景 | 结果 | 证据 |','|---|---|---|---|',
    *[f'| {r["lane"]} | {r["name"]} | {r["status"]} | {r.get("detail","").replace(chr(10)," ").replace("|","/")[:450]} |' for r in data['scenarios']],
    '', '实际用量（缓存输入为输入子集）：`'+json.dumps(data['usage'])+'`。',
    '只有必测项全部通过才允许发布；功能失败、基础设施阻塞和未覆盖均不计通过。'])+'\n'
write(root/'candidate-report.zh-CN.md',text)
raise SystemExit(exit_code)
