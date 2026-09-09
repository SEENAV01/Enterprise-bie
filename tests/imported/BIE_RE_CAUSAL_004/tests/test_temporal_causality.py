import unittest
from bie.reasoning.temporal_causality import *
class T(unittest.TestCase):
 def test_valid(self):self.assertTrue(validate_temporal(1,3,1,3)["valid"])
 def test_reverse(self):self.assertFalse(validate_temporal(3,1)["valid"])
 def test_max(self):self.assertFalse(validate_temporal(1,10,0,5)["valid"])
 def test_bad(self):
  with self.assertRaises(ValueError):validate_temporal(1,2,5,2)
