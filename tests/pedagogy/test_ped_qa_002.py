import unittest
from bie.pedagogy.prerequisite_coverage_qa import prerequisite_coverage_qa

class TestPrerequisiteCoverageQA(unittest.TestCase):
    def test_low_unbridged_blocks(self):
        r=prerequisite_coverage_qa(["p"],{"p":.4},[])
        self.assertFalse(r.passed)
        self.assertEqual(r.unbridged_prerequisites,("p",))

    def test_bridge_allows(self):
        self.assertTrue(prerequisite_coverage_qa(["p"],{"p":.4},["p"]).passed)
