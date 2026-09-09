import unittest
from app.bie.reasoning.representation_decision import *
class T(unittest.TestCase):
 def test_pick(self):self.assertEqual(decide([Candidate("text",.5,.8,"e"),Candidate("graph",1,.7,"e")]).kind,"graph")
 def test_evidence(self):
  with self.assertRaises(ValueError):decide([Candidate("x",1,1,"")])
 def test_empty(self):
  with self.assertRaises(ValueError):decide([])
 def test_range(self):
  with self.assertRaises(ValueError):decide([Candidate("x",2,1,"e")])
