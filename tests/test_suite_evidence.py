import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from suite_verify import tdd_order


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

    def test_skill_read_is_not_test_execution(self):
        records=[{'command':'cat test-driven-development/SKILL.md','exit_code':1,'aggregated_output':'FAILED (errors=1)'},
                 {'command':'cat unittest-guide.md','exit_code':0,'aggregated_output':'Ran 3 tests\nOK'}]
        self.assertFalse(tdd_order(records))
