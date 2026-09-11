import unittest
from bie.reasoning.temporal_nested_interval_reasoning import *
class T(unittest.TestCase):
 def test_within(self): self.assertEqual(interval_relation(Interval(2,3),Interval(1,5)),"A_WITHIN_B")
 def test_contains(self): self.assertEqual(interval_relation(Interval(1,5),Interval(2,3)),"B_WITHIN_A")
 def test_equal(self): self.assertEqual(interval_relation(Interval(1,5),Interval(1,5)),"EQUAL")
 def test_overlap(self): self.assertEqual(interval_relation(Interval(1,4),Interval(3,6)),"OVERLAP")
 def test_disjoint(self): self.assertEqual(interval_relation(Interval(1,2),Interval(3,4)),"DISJOINT")
 def test_invalid(self):
  with self.assertRaises(ValueError): interval_relation(Interval(5,1),Interval(1,2))
