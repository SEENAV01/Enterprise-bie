import unittest
from bie.reasoning.animation_decision import *
class T(unittest.TestCase):
 def test_pick(self):self.assertEqual(decide([Animation("decorative",.1,.9,"e"),Animation("trace",1,.2,"e")]).intent,"trace")
 def test_empty(self):
  with self.assertRaises(ValueError):decide([])
 def test_range(self):
  with self.assertRaises(ValueError):decide([Animation("x",2,0,"e")])
 def test_evidence(self):
  with self.assertRaises(ValueError):decide([Animation("x",1,0,"")])
