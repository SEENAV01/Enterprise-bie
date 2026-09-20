import unittest
from bie.visual_intelligence.complexity_budget import *
def s(**kw):
 d=dict(required_semantic_ids=("a","b"),element_count=5,text_chars=100,asset_bytes=100000,vector_ops=20,animation_tracks=2,three_d_objects=0,particle_count=0,simulation_steps=0);d.update(kw);return SceneComplexity(**d)
def p():return BudgetProfile("web",20,35,5_000_000,2,5000)
class T(unittest.TestCase):
 def test_pass(self):self.assertEqual(evaluate_budget(s(),p()).action,"PASS")
 def test_simplify(self):self.assertEqual(evaluate_budget(s(asset_bytes=8_000_000),p()).action,"SIMPLIFY")
 def test_split(self):self.assertEqual(evaluate_budget(s(three_d_objects=10,animation_tracks=30),p()).action,"SPLIT_SCENE")
 def test_preserve(self):self.assertTrue(assert_semantics_preserved(evaluate_budget(s(),p()),["a","b","c"]))
 def test_loss(self):
  with self.assertRaises(ComplexityBudgetError):assert_semantics_preserved(evaluate_budget(s(),p()),["a"])
 def test_negative(self):
  with self.assertRaises(ComplexityBudgetError):estimate_complexity(s(element_count=-1))
 def test_hint(self):self.assertIn("compress_or_reuse_assets",evaluate_budget(s(asset_bytes=8_000_000),p()).simplification_hints)
 def test_not_accepted(self):self.assertFalse(evaluate_budget(s(),p()).accepted)
