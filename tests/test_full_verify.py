import json
from pathlib import Path
import os
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from full_verify import task_adapter_check, tests_pass, skill_read, usage
from sanitize import redact
from suite_verify import rows


class FullEvidenceTests(unittest.TestCase):
    def test_no_tests_is_not_success(self):
        self.assertFalse(tests_pass({'exit_code':0,'stdout':'Ran 0 tests\nOK','stderr':''}))
        self.assertTrue(tests_pass({'exit_code':0,'stdout':'','stderr':'Ran 8 tests\nOK'}))

    def test_failed_skill_read_does_not_prove_skill_use(self):
        command='cat skills/systematic-debugging/SKILL.md'
        self.assertFalse(skill_read([{'command':command,'exit_code':1}],'systematic-debugging'))
        self.assertTrue(skill_read([{'command':command,'exit_code':0}],'systematic-debugging'))

    def test_adapter_requires_exact_description_and_canonical_identity(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'scratch/a.md';p.parent.mkdir()
            canonical='- [ ] T001 First\n- [ ] T002 Second\n'
            p.write_text('### Task 1: T002\n- [ ] T002 Second\n')
            self.assertTrue(task_adapter_check(d,canonical,['T002'])[0])
            self.assertFalse(task_adapter_check(d,canonical,['T001'])[0])
            p.write_text('### Task 1: T002\n- [ ] T002 Different\n')
            self.assertFalse(task_adapter_check(d,canonical,['T002'])[0])

    def test_usage_deduplicates_session_snapshots_and_does_not_add_cache_twice(self):
        with tempfile.TemporaryDirectory() as d:
            for sub in ['a','b']:
                p=Path(d)/sub/'rollout-copy.jsonl';p.parent.mkdir()
                events=[{'type':'session_meta','payload':{'id':'same-session'}},
                        {'type':'event_msg','payload':{'type':'token_count','info':{'total_token_usage':{
                            'input_tokens':100,'cached_input_tokens':75,'output_tokens':4}}}}]
                p.write_text('\n'.join(json.dumps(e) for e in events))
            result=usage(d)
            self.assertEqual(result['input_tokens'],100)
            self.assertEqual(result['non_cached_input_tokens'],25)
            self.assertEqual(result['session_count'],1)

    def test_github_tokens_are_redacted_before_public_evidence(self):
        with patch.dict(os.environ,{'GITHUB_TOKEN':'test-hidden-token'}):
            self.assertEqual(redact('test-hidden-token'), '[REDACTED]')
        self.assertEqual(redact('ghp_'+'a'*30),'[REDACTED]')

    def test_native_powershell_utf8_bom_events_parse(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'events.jsonl'
            p.write_text('{"status":"ready"}\n',encoding='utf-8-sig')
            self.assertEqual(rows(p),[{'status':'ready'}])


if __name__=='__main__':unittest.main()
