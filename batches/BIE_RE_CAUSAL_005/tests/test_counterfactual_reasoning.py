import unittest
from app.bie.reasoning.counterfactual_reasoning import *
class T(unittest.TestCase):
 def test_change(self):self.assertTrue(assess("remove A","B","not B",["e"]).changed)
 def test_same(self):self.assertFalse(assess("alter A","B","B",["e"]).changed)
 def test_evidence(self):
  with self.assertRaises(ValueError):assess("x","a","b",[])
 def test_blank(self):
  with self.assertRaises(ValueError):assess("","a","b",["e"])
