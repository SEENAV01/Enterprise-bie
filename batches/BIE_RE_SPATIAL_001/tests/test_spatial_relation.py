import unittest
from app.bie.reasoning.spatial_relation import *
class T(unittest.TestCase):
 def test_valid(self):self.assertEqual(relation("A","left_of","B",["e"])[1],"left_of")
 def test_type(self):
  with self.assertRaises(ValueError):relation("A","nearish","B",["e"])
 def test_evidence(self):
  with self.assertRaises(ValueError):relation("A","above","B",[])
 def test_self(self):
  with self.assertRaises(ValueError):relation("A","left_of","A",["e"])
