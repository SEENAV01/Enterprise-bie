import unittest
from bie.visual_intelligence.visual_qa_contracts import make_result
from bie.visual_intelligence.visual_benchmark import *
def r(dim,s=1.0,b=()): return make_result(dim,dim,s,b,(),["e"],["r"],{})
def good(): return [r("semantic_alignment"),r("layout_qa"),r("clutter_qa"),r("asset_qa")]
class T(unittest.TestCase):
 def test_pass(self): self.assertTrue(evaluate_visual_benchmark(good()).passed)
 def test_floor(self):
  x=good();x[0]=r("semantic_alignment",.8);self.assertIn("semantic_alignment",evaluate_visual_benchmark(x).hard_floor_failures)
 def test_blocker(self):
  x=good();x[1]=r("layout_qa",1,("collision",));self.assertFalse(evaluate_visual_benchmark(x).passed)
 def test_missing(self):
  with self.assertRaises(VisualBenchmarkError): evaluate_visual_benchmark(good()[:-1])
 def test_score(self): self.assertEqual(evaluate_visual_benchmark(good()).weighted_score,1.0)
 def test_not_accepted(self): self.assertFalse(evaluate_visual_benchmark(good()).accepted)
 def test_deterministic(self): self.assertEqual(evaluate_visual_benchmark(good()).fingerprint,evaluate_visual_benchmark(good()).fingerprint)
