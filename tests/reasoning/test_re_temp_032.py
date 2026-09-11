import unittest
from bie.reasoning.temporal_change_point_reasoning import *
class T(unittest.TestCase):
 def test_detect(self): self.assertEqual(detect_change_points([Observation(1,1),Observation(2,5)],min_delta=3)[0].delta,4)
 def test_ignore(self): self.assertEqual(detect_change_points([Observation(1,1),Observation(2,2)],min_delta=2),())
 def test_sort(self): self.assertEqual(detect_change_points([Observation(2,5),Observation(1,1)],min_delta=3)[0].time,2)
 def test_duplicate(self):
  with self.assertRaises(ValueError): detect_change_points([Observation(1,1),Observation(1,2)],min_delta=0)
 def test_bad_delta(self):
  with self.assertRaises(ValueError): detect_change_points([],min_delta=-1)
