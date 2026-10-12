"""Merge two platform results without grading any missing evidence as success."""
import json
from pathlib import Path
import sys
from fixtures import write


def main(root):
    root=Path(root);results=[];usages=[]
    for lane in ['latest-linux','latest-windows']:
        directory=root/lane
        if (directory/'results.json').exists():
            results.append(json.loads((directory/'results.json').read_text(encoding='utf-8')))
        else:
            results.append({'lane':lane,'model_calls':0,'reviewer_spawns':0,'scenarios':[
                {'name':'platform evidence','status':'not_covered','detail':'No platform evidence; inspect job prerequisites'}]})
        if (directory/'full-usage.json').exists():
            usages.append(json.loads((directory/'full-usage.json').read_text(encoding='utf-8')))
    calls=sum(r['model_calls'] for r in results);reviews=sum(r['reviewer_spawns'] for r in results)
    combined={k:sum(r.get(k,0) for r in usages) for k in ['input_tokens','cached_input_tokens','non_cached_input_tokens','output_tokens','session_count']}
    scenarios=[{'lane':r['lane'],**s} for r in results for s in r['scenarios']]
    counts={s:sum(r['status']==s for r in scenarios) for s in ['pass','fail','blocked','not_covered']}
    budget=calls<=20 and reviews<=6
    output={'model_calls':calls,'reviewer_spawns':reviews,'budget_ok':budget,'limits':{'calls':20,'reviews':6},
            'versions':{'bridge':'1.3.0','spec_kit':'1.1.3','superpowers':'7.0.0','codex':'0.162.1'},
            'counts':counts,'usage':combined,'scenarios':scenarios,'platforms':results}
    write(root/'full-results.json',json.dumps(output,ensure_ascii=False,indent=2))
    text='\n'.join(['# Codex 原版完整桥接测试汇总','',
        '**组合**：Bridge 1.3.0 / SK 1.1.3 / SP 7.0.0 / Codex CLI 0.162.1。',
        '**模型**：gpt-6.1-sol，低推理；Linux 和 Windows 顺序执行。',
        f'新增主调用 **{calls}/20**，审查 **{reviews}/6**。预算检查：{budget}。',
        f'结果：{counts}。功能失败、权限阻塞和未覆盖均不能算通过。','',
        '| 平台 | 场景 | 结果 | 说明 |','|---|---|---|---|',
        *[f'| {r["lane"]} | {r["name"]} | {r["status"]} | {r.get("detail","").replace(chr(10)," ").replace("|","/")[:500]} |' for r in scenarios],
        '', '## Token 计量','',
        '`'+json.dumps(combined)+'`。缓存输入是输入子集，不重复相加；不推算网关实际扣费。','',
        '## 判断范围','',
        '此报告只证明列出的原版版本、平台、固定小项目和异常场景。不代表 Claude Code、部署或任意插件组合。',
        '已知缺必需文档仍 ready 的行为保留真实失败，不修补上游，也不降低验收标准。',
        '只有必测项全部完成并通过，才可宣称完整兼容。'])+'\n'
    write(root/'full-report.zh-CN.md',text)
    return 0 if budget and not any(counts[k] for k in ['fail','blocked','not_covered']) else 1


if __name__=='__main__':raise SystemExit(main(sys.argv[1]))
