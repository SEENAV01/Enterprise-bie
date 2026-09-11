import unittest
from bie.reasoning.temporal_fuzzy_expression import *
class T(unittest.TestCase):
 def test_bounds(self): self.assertEqual(bounds(FuzzyTime(10,2)),(8,12))
 def test_before(self): self.assertEqual(fuzzy_relation(FuzzyTime(1,1),FuzzyTime(5,1)),"DEFINITELY_BEFORE")
 def test_overlap(self): self.assertEqual(fuzzy_relation(FuzzyTime(5,2),FuzzyTime(6,2)),"OVERLAP_OR_UNCERTAIN")
 def test_after(self): self.assertEqual(fuzzy_relation(FuzzyTime(10,1),FuzzyTime(2,1)),"DEFINITELY_AFTER")
 def test_bad(self):
  with self.assertRaises(ValueError): bounds(FuzzyTime(1,-1))
