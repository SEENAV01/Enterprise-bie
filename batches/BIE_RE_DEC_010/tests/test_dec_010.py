import unittest
from app.bie.reasoning.remediation_decision import *
class T(unittest.TestCase):
 def test_bridge(self):self.assertEqual(decide(Gap("x",.8,1,0)),"bridge_prerequisite")
 def test_mis(self):self.assertEqual(decide(Gap("x",.5,0,1)),"misconception_confrontation")
 def test_reteach(self):self.assertEqual(decide(Gap("x",.8,0,0)),"reteach_with_new_representation")
 def test_bad(self):
  with self.assertRaises(ValueError):decide(Gap("x",2,0,0))
