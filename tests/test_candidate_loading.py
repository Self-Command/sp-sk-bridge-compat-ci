"""Catch controller import failures before a paid Actions regression starts."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))


class CandidateLoadingTests(unittest.TestCase):
    def test_candidate_controller_imports_with_existing_evidence_api(self):
        import run_candidate_suite
        self.assertTrue(issubclass(run_candidate_suite.CandidateSuite,run_candidate_suite.FullSuite))

    def test_selective_continuation_imports_before_paid_work(self):
        import continue_candidate_suite
        self.assertTrue(issubclass(continue_candidate_suite.ContinuedCandidate,continue_candidate_suite.CandidateSuite))

