import unittest
from bie.reasoning.temporal_realbook_fixture_harness import *

class T(unittest.TestCase):
    def fixture(self):
        return TemporalFixture("f1","src1","When?","RESOLVED",("e1","e2"))
    def test_pass(self):
        self.assertTrue(evaluate_fixture(self.fixture(),"RESOLVED",["e2","e1"]).passed)
    def test_status_fail(self):
        self.assertIn("status_mismatch",evaluate_fixture(self.fixture(),"AMBIGUOUS",["e1","e2"]).reasons)
    def test_evidence_fail(self):
        self.assertTrue(evaluate_fixture(self.fixture(),"RESOLVED",["e1"]).reasons[0].startswith("missing_required_evidence"))
    def test_summary(self):
        s=summarize_fixture_outcomes([FixtureOutcome("a",True,()),FixtureOutcome("b",False,("x",))])
        self.assertEqual(s,{"total":2,"passed":1,"failed":1})
