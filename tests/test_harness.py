import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from verify import evidence_flags, immutable_artifacts, tasks
from sanitize import redact


class EvidenceTests(unittest.TestCase):
    def test_claim_is_not_tool_evidence(self):
        event = {'item': {'type':'agent_message','text':'Read executing-plans SKILL.md, tests passed'}}
        flags = evidence_flags(json.dumps(event))
        self.assertFalse(flags['native_executor_read'])
        self.assertFalse(flags['green'])

    def test_progress_is_not_requirement_drift(self):
        before={'tasks.md':'- [ ] T001 Add 100 character titles\n'}
        after={'tasks.md':'- [x] T001 Add 100 character titles\n'}
        self.assertTrue(immutable_artifacts(before,after)['tasks.md'])
        after={'tasks.md':'- [x] T001 Add 5 character titles\n'}
        self.assertFalse(immutable_artifacts(before,after)['tasks.md'])

    def test_stable_canonical_ids(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'tasks.md'
            path.write_text('- [x] T001 First\n- [ ] T007 Later\n')
            self.assertEqual(tasks(path), [('T001', True, 'First'),('T007',False,'Later')])

    def test_secret_shape_redacted(self):
        self.assertEqual(redact('x nb_'+'a'*30+' y'), 'x [REDACTED] y')


if __name__ == '__main__':
    unittest.main()
