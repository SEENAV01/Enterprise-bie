import unittest
from bie.reasoning.misconception_decision import decide
class T(unittest.TestCase):
 def test_high(self):self.assertEqual(decide(1,1,["e"])[2],"explicit_confrontation")
 def test_mid(self):self.assertEqual(decide(.5,.5,["e"])[2],"diagnostic_check")
 def test_low(self):self.assertFalse(decide(.1,.1,["e"])[0])
 def test_evidence(self):
  with self.assertRaises(ValueError):decide(.5,.5,[])
