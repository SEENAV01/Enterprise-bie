import unittest
from app.bie.reasoning.simulation_decision import *
class T(unittest.TestCase):
 def test_pick(self):self.assertEqual(decide([Candidate("static",.3,0,"e"),Candidate("sim",1,1,"e")]).kind,"sim")
 def test_empty(self):
  with self.assertRaises(ValueError):decide([])
 def test_evidence(self):
  with self.assertRaises(ValueError):decide([Candidate("x",1,1,"")])
 def test_range(self):
  with self.assertRaises(ValueError):decide([Candidate("x",2,1,"e")])
