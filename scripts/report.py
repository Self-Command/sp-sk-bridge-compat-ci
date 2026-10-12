"""Combine deterministic lane results; do not ask a model to grade itself."""
import json
import os
from pathlib import Path
import sys


def report(root):
    root = Path(root)
    results = [json.loads(p.read_text()) for p in sorted(root.glob('*/results.json'))]
    rows = []
    calls = spawns = 0
    prior=[json.loads(p.read_text()) for p in (Path(__file__).resolve().parents[1]/'prior-runs').glob('*-summary.json')]
    calls+=sum(p.get('model_calls',0) for p in prior)
    spawns+=sum(p.get('reviewer_spawns',0) for p in prior)
    for lane in results:
        calls += lane.get('model_calls', 0)
        spawns += lane.get('reviewer_spawns', 0)
        for case in lane.get('scenarios', []):
            detail = str(case.get('detail', '')).replace('|', '/').replace('\n', ' ')
            rows.append(f"| {lane['lane']} | {case['name']} | {case['status']} | {detail} |")
    statuses = [s['status'] for r in results for s in r.get('scenarios', [])]
    missing = sorted({'latest-linux', 'latest-windows', 'baseline-linux'} - {r['lane'] for r in results})
    if any(s == 'fail' for s in statuses):
        verdict = 'Compatibility defects observed: see individual scenarios and baseline comparison. Coverage may be incomplete.'
    elif not results or missing or any(s == 'blocked' for s in statuses):
        verdict = 'Infrastructure or evidence blockage: see scenario rows; no blanket compatibility claim.'
    else:
        verdict = 'All executed scenarios passed. Check coverage and lane completeness below.'
    usage={'input_tokens':0,'cached_input_tokens':0,'output_tokens':0}
    for previous in prior:
        for key in usage:
            usage[key]+=previous.get('usage',{}).get(key,0)
    for path in root.glob('*/*/process.json'):
        process=json.loads(path.read_text())
        for turn in process.get('usage',[]):
            for key in usage:
                usage[key]+=turn.get(key,0)
    text = '\n'.join([
        '# Bridge compatibility report', '', verdict, '',
        f'Top-level Codex calls: {calls}/20; reviewer spawns: {spawns}/12.',
        'Totals include the retained first-run probe and controller-failure evidence.',
        f'Missing lanes: {missing or "none"}.', '',
        f'Client-reported token totals: {usage}. Cached input is a subset of input.', '',
        '| Lane | Scenario | Result | Evidence finding |',
        '|---|---|---|---|', *rows, '',
        'The requested model is gpt-6.1-sol throughout. Client/session metadata cannot independently prove gateway backend identity.',
        'Reports and fixture files are evidence; model success claims and handoff complete alone are insufficient.',
    ]) + '\n'
    root.mkdir(parents=True, exist_ok=True)
    (root/'compatibility-report.md').write_text(text, encoding='utf-8')
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as stream:
            stream.write(text)
    print(text)
    return text


if __name__ == '__main__':
    report(sys.argv[1])
