import unittest
from app.bie.reasoning.uncertainty import *
class T(unittest.TestCase):
 def test_high(self):self.assertEqual(represent(1,1,0)["label"],"high")
 def test_conflict(self):self.assertLess(represent(1,1,1)["confidence"],1)
 def test_low(self):self.assertEqual(represent(1,.2,0)["label"],"low")
 def test_bad(self):
  with self.assertRaises(ValueError):represent(2,1,0)
