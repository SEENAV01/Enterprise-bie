import unittest
from app.bie.reasoning.causal_chain import *
class T(unittest.TestCase):
 def test_chain(self):self.assertEqual(len(build_chain([CausalStep("A","B","m1","e1"),CausalStep("B","C","m2","e2")])),2)
 def test_gap(self):
  with self.assertRaises(ValueError):build_chain([CausalStep("A","B","m","e"),CausalStep("X","C","m","e")])
 def test_empty(self):
  with self.assertRaises(ValueError):build_chain([])
 def test_ground(self):
  with self.assertRaises(ValueError):build_chain([CausalStep("A","B","","e")])
