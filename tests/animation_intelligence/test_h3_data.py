import unittest
from bie.animation_intelligence.data_animation_grammar import *
def S(i="s",u=None):return DataSeries(i,((0,1),(1,2)),("src",),u)
class T(unittest.TestCase):
 def test_pass(self):self.assertEqual(plan_series_transition("p",S(),S()).status,"PASS")
 def test_identity(self):self.assertEqual(plan_series_transition("p",S("a"),S("b")).status,"BLOCKED")
 def test_uncertainty(self):self.assertEqual(plan_series_transition("p",S(u=((.8,1.2),(1.8,2.2))),S(u=((.9,1.1),(1.9,2.1))),preserve_uncertainty=False).status,"BLOCKED")
 def test_causal_review(self):self.assertEqual(plan_series_transition("p",S(),S(),claim="causal").status,"REVIEW")
 def test_bad_points(self):
  with self.assertRaises(DataAnimationError):plan_series_transition("p",DataSeries("s",((0,float("nan")),(1,2)),("src",)),S())
 def test_distribution(self):self.assertEqual(plan_distribution_reveal("d",({"value":.5},{"value":.5}),source_refs=("s",),normalized=True).status,"PASS")
 def test_distribution_review(self):self.assertEqual(plan_distribution_reveal("d",({"value":.2},{"value":.2}),source_refs=("s",),normalized=True).status,"REVIEW")
 def test_not_accepted(self):self.assertFalse(plan_series_transition("p",S(),S()).accepted)
