import unittest
from bie.reasoning.temporal_quality_gate import *
class T(unittest.TestCase):
 def test_pass(self): self.assertTrue(evaluate_temporal_quality(TemporalQualitySignals(True,True,.9,True)).passed)
 def test_grounding(self): self.assertIn("ungrounded",evaluate_temporal_quality(TemporalQualitySignals(False,True,.9,True)).blockers)
 def test_multiple(self): self.assertEqual(len(evaluate_temporal_quality(TemporalQualitySignals(False,False,.2,False,1)).blockers),5)
 def test_bad_conf(self):
  with self.assertRaises(ValueError): evaluate_temporal_quality(TemporalQualitySignals(True,True,2,True))
 def test_bad_count(self):
  with self.assertRaises(ValueError): evaluate_temporal_quality(TemporalQualitySignals(True,True,.8,True,-1))
