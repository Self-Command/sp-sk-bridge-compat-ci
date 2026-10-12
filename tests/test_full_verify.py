import json
from pathlib import Path
import os
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from full_verify import contract_ok, task_adapter_check, tests_pass, skill_read, test_suite, usage, yaml_problem_reported
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

    def test_later_batch_failure_requires_entire_original_skill_in_output(self):
        content='---\nname: brainstorming\n---\n# Brainstorming\nAll native instructions.\n'
        item={'command':'Get-Content skills/brainstorming/SKILL.md; rg absent-name',
              'exit_code':1,'aggregated_output':content.replace('\n','\r\n')}
        self.assertTrue(skill_read([item],'brainstorming',content))
        item['aggregated_output']='# Brainstorming\nI read the skill.'
        self.assertFalse(skill_read([item],'brainstorming',content))

    def test_generated_root_and_nested_test_layouts_both_run_nonempty_tests(self):
        for nested in (False,True):
            with self.subTest(nested=nested),tempfile.TemporaryDirectory() as d:
                directory=Path(d)/'tests' if nested else Path(d)
                directory.mkdir(exist_ok=True)
                self.assertFalse(tests_pass(test_suite(d)))
                (directory/'test_fixture.py').write_text('import unittest\nclass Probe(unittest.TestCase):\n def test_actual(self):self.assertEqual(2+2,4)\n')
                self.assertTrue(tests_pass(test_suite(d)))

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

    def test_external_fault_recovery_log_preserves_original_contract(self):
        path='specs/001/tasks.md'
        old={path:'- [ ] T001 Implement normalize_title; record evidence in tasks.md.\n'}
        appendix='\n## T001 execution evidence\nRED exit 1; GREEN exit 0.\n\n## Recovery of injected product fault\n\n- Tests exit 1; removed external normalize_title rebinding; tests exit 0.\n'
        new={path:old[path].replace('[ ]','[x]')+appendix}
        self.assertTrue(contract_ok(old,new))
        self.assertTrue(contract_ok({k.replace('/','\\'):v for k,v in old.items()},
                                    {k.replace('/','\\'):v for k,v in new.items()}))
        self.assertFalse(contract_ok(old,{path:new[path].replace('Implement normalize_title','Implement other')}))
        self.assertFalse(contract_ok(old,{path:new[path]+'- [ ] T004 New requirement\n'}))
        self.assertFalse(contract_ok(old,{path:new[path].replace('tests exit 0.','MUST add persistence; tests exit 0.')}))
        final='\n## Final verification and review\n- Task commits: T001 abc123.\n- One reviewer passed 15 tests.\n'
        self.assertTrue(contract_ok(old,{path:new[path]+final}))
        self.assertFalse(contract_ok(old,{path:new[path]+final+'MUST add persistence.\n'}))

    def test_actual_parser_diagnostic_does_not_require_its_class_name(self):
        broken='hooks: [ deliberately invalid: [\n'
        self.assertTrue(yaml_problem_reported("expected the node content, but found '<stream end>'",broken))
        self.assertFalse(yaml_problem_reported('YAML malformed; continue.',broken))
        self.assertFalse(yaml_problem_reported('expected the node content', 'hooks: []'))


if __name__=='__main__':unittest.main()
