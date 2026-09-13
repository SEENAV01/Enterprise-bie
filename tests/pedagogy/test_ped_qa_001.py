import unittest
from bie.pedagogy.objective_coverage_qa import objective_coverage_qa

class TestObjectiveCoverageQA(unittest.TestCase):
    def test_missing_objective_blocks(self):
        r=objective_coverage_qa({"o1":["a"]},["o1","o2"])
        self.assertFalse(r.passed)
        self.assertEqual(r.uncovered_objectives,("o2",))

    def test_full_coverage(self):
        self.assertTrue(objective_coverage_qa({"o1":["a"]},["o1"]).passed)
