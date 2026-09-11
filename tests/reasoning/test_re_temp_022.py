import unittest
from bie.reasoning.temporal_missing_event_reasoning import *
class T(unittest.TestCase):
 def test_gap(self): self.assertEqual(detect_temporal_gaps([1,2,10],threshold=3)[0].duration,8)
 def test_no_gap(self): self.assertEqual(detect_temporal_gaps([1,2,3],threshold=2),())
 def test_sorted(self): self.assertEqual(detect_temporal_gaps([10,1,2],threshold=3)[0].right,10)
 def test_dedup(self): self.assertEqual(detect_temporal_gaps([1,1,5],threshold=2)[0].left,1)
 def test_bad_threshold(self):
  with self.assertRaises(ValueError): detect_temporal_gaps([1,2],threshold=-1)
