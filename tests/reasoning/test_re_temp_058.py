import unittest
from bie.reasoning.temporal_staged_regression_plan import *

class T(unittest.TestCase):
    def good(self):
        return {s.name:True for s in MANDATORY_STAGES}
    def test_pass(self):
        self.assertTrue(evaluate_regression_results(self.good())["ready"])
    def test_missing(self):
        r=self.good(); r.pop("enterprise_runner")
        self.assertEqual(evaluate_regression_results(r)["status"],"MISSING_STAGE")
    def test_failed(self):
        r=self.good(); r["import_smoke"]=False
        self.assertEqual(evaluate_regression_results(r)["status"],"FAILED_STAGE")
    def test_stage_count(self):
        self.assertGreaterEqual(len(MANDATORY_STAGES),5)
