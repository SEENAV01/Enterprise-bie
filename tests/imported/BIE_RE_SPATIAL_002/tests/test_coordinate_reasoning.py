import unittest
from bie.reasoning.coordinate_reasoning import *
class T(unittest.TestCase):
 def test_distance(self):self.assertEqual(analyze((0,0),(3,4))["distance"],5)
 def test_right(self):self.assertEqual(analyze((0,0),(1,0))["direction"][0],"right")
 def test_down(self):self.assertEqual(analyze((0,1),(0,0))["direction"][1],"down")
 def test_bad(self):
  with self.assertRaises(ValueError):analyze((0,), (1,2))
