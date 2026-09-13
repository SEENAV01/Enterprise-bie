import unittest
from bie.pedagogy.explanation_mode import plan_explanation

class TestExplanationMode(unittest.TestCase):
    def test_sequence_contains_mechanism_and_check(self):
        r=plan_explanation("c","definition","mechanism","example",["e"])
        self.assertTrue(any("mechanism" in x for x in r.sequence))
        self.assertIn("check understanding",r.sequence)
