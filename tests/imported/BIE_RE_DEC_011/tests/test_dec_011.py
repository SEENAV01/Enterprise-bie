import unittest
from bie.reasoning.visual_decision import *
class T(unittest.TestCase):
 def test_pick(self):self.assertEqual(decide([Visual("text",.3,.5,0,"e"),Visual("diagram",1,.5,.5,"e")]).kind,"diagram")
 def test_empty(self):
  with self.assertRaises(ValueError):decide([])
 def test_evidence(self):
  with self.assertRaises(ValueError):decide([Visual("x",1,.5,.5,"")])
 def test_range(self):
  with self.assertRaises(ValueError):decide([Visual("x",2,.5,.5,"e")])
