import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from suite_verify import tdd_order, preserved_contracts


class SuiteEvidenceTests(unittest.TestCase):
    def test_empty_suite_does_not_prove_red_or_green(self):
        records=[{'command':'python -m unittest discover','exit_code':5,'aggregated_output':'Ran 0 tests\nNO TESTS RAN'},
                 {'command':'python -m unittest discover','exit_code':0,'aggregated_output':'Ran 0 tests\nOK'}]
        self.assertFalse(tdd_order(records))

    def test_failure_followed_by_real_pass_proves_tdd(self):
        red={'command':'python -m unittest discover -s tests -v','exit_code':1,'aggregated_output':'Ran 1 test\nFAILED (errors=1)'}
        green={'command':'python -m unittest discover -s tests -v','exit_code':0,'aggregated_output':'Ran 3 tests\nOK'}
        self.assertTrue(tdd_order([red,green]))
        self.assertFalse(tdd_order([green,red]))

    def test_later_shell_success_does_not_erase_actual_failed_test_run(self):
        red={'command':'python -m unittest -v test_app; git status --short',
             'exit_code':0,'aggregated_output':'Ran 2 tests in 0.1s\nFAILED (failures=1)\nclean branch'}
        green={'command':'python -m unittest discover -v',
               'exit_code':0,'aggregated_output':'Ran 2 tests in 0.1s\nOK'}
        self.assertTrue(tdd_order([red,green]))
        self.assertFalse(tdd_order([green,red]))
        red['aggregated_output']='Assertion: expected red first.'
        self.assertFalse(tdd_order([red,green]))

    def test_skill_read_is_not_test_execution(self):
        records=[{'command':'cat test-driven-development/SKILL.md','exit_code':1,'aggregated_output':'FAILED (errors=1)'},
                 {'command':'cat unittest-guide.md','exit_code':0,'aggregated_output':'Ran 3 tests\nOK'}]
        self.assertFalse(tdd_order(records))

    def test_explicit_task_evidence_is_allowed_but_requirement_changes_are_not(self):
        old={'specs/001/tasks.md':'# Tasks\n- [ ] T001 Implement add and preserve execution evidence in tasks.md.\n'}
        evidence='\n## T001 execution evidence\nRED failed; GREEN passed.\n'
        new={'specs/001/tasks.md':old['specs/001/tasks.md'].replace('[ ]','[x]')+evidence}
        self.assertTrue(all(preserved_contracts(old,new).values()))
        new['specs/001/tasks.md']=new['specs/001/tasks.md'].replace('Implement add','Implement subtract')
        self.assertFalse(all(preserved_contracts(old,new).values()))

    def test_unrequested_appendix_cannot_change_contract(self):
        old={'specs/001/tasks.md':'- [ ] T001 Implement add.\n'}
        new={'specs/001/tasks.md':old['specs/001/tasks.md']+'\n## T001 execution evidence\nDone.\n'}
        self.assertFalse(all(preserved_contracts(old,new).values()))

    def test_record_red_green_progress_is_legal_without_changed_task_requirements(self):
        old={'specs/002/tasks.md':'- [ ] T001 Implement subtract; record red/green commands and results in tasks.md.\nImplementation remains pending.\n'}
        new={'specs/002/tasks.md':old['specs/002/tasks.md'].replace('[ ]','[x]').replace('Implementation remains pending.','Implementation evidence follows.')+'\n## T001 execution evidence\nRED failed, GREEN passed.\n'}
        self.assertTrue(all(preserved_contracts(old,new).values()))
        new['specs/002/tasks.md']=new['specs/002/tasks.md'].replace('subtract','multiply')
        self.assertFalse(all(preserved_contracts(old,new).values()))
