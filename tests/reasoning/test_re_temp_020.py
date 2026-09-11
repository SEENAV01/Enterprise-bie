import unittest
from bie.reasoning.temporal_counterfactual_guard import *
class T(unittest.TestCase):
 def test_valid(self): self.assertTrue(assess_temporal_counterfactual(TemporalCounterfactual(5,10,1)).admissible)
 def test_before(self): self.assertIn("violates_required_before",assess_temporal_counterfactual(TemporalCounterfactual(10,10,None)).reasons)
 def test_after(self): self.assertIn("violates_required_after",assess_temporal_counterfactual(TemporalCounterfactual(1,None,1)).reasons)
 def test_bad_bounds(self): self.assertIn("inconsistent_bounds",assess_temporal_counterfactual(TemporalCounterfactual(5,4,6)).reasons)
