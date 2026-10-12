"""Correct only two retrieval bugs using existing immutable model evidence."""
from pathlib import Path
import json
import sys

from fixtures import write
from full_verify import records,yaml_problem_reported
from suite_verify import injected_skills


def main(root):
    root=Path(root);changes=[]
    for lane in ('latest-linux','latest-windows'):
        directory=root/lane
        path=directory/'results.json'
        data=json.loads(path.read_text())
        write(directory/'unadjusted-final-results.json',json.dumps(data,indent=2))
        for row in data['scenarios']:
            if row['name']=='bridge convergence actual verification and original SK skill unchanged':
                key='installed_entry_used'
                value='speckit-speckit-superpowers-bridge-converge' in injected_skills(directory/'sessions')
                reason='Inspect final exported sessions; the controller initially inspected a stale pre-convergence export.'
            elif row['name']=='malformed hook registry lifecycle':
                key='parser_error_reported'
                text=(directory/'10-hook-registry-variants/last-message.md').read_text()
                for line in (directory/'10-hook-registry-variants/events.jsonl').read_text().splitlines():
                    event=json.loads(line);item=event.get('item',{})
                    if event.get('type')=='item.completed':
                        text+='\n'+item.get('text',item.get('aggregated_output',''))
                value=yaml_problem_reported(text,'hooks: [ deliberately invalid: [\n')
                reason='Actual full parser diagnostic was emitted earlier; the concise final summary did not repeat it.'
            else:continue
            old=row['checks'][key]
            row['checks'][key]=value
            row['status']='pass' if all(row['checks'].values()) else 'fail'
            row['detail']=json.dumps(row['checks'],ensure_ascii=False)
            row['regrade_reason']=reason
            changes.append({'lane':lane,'scenario':row['name'],'check':key,
                            'before':old,'after':value,'reason':reason})
        write(path,json.dumps(data,ensure_ascii=False,indent=2))
        text='\n'.join(['# Bridge v1.4.0 Codex 实测：'+lane,'',
            '固定 SK 1.1.3 / SP 7.0.0 / Codex CLI 0.162.1 / gpt-6.1-sol、low。',
            f'累计主调用 {data["model_calls"]}，审查 {data["reviewer_spawns"]}。','',
            '| 场景 | 结果 | 证据 |','|---|---|---|',
            *[f'| {r["name"]} | {r["status"]} | {r["detail"].replace(chr(10)," ").replace("|","/")[:500]} |' for r in data['scenarios']],
            '', '更正项见 regraded-checks.json；原结果保存在 unadjusted-final-results.json。',
            '更正只读取既有原始命令与会话证据，没有新增模型调用或修改产品/上游技能。'])+'\n'
        write(directory/'full-report.zh-CN.md',text)
    write(root/'regraded-checks.json',json.dumps(changes,ensure_ascii=False,indent=2))
    print(json.dumps(changes,ensure_ascii=False))


if __name__=='__main__':main(sys.argv[1])
