import unittest
from bie.knowledge_intelligence.boundary_cases import *
class T(unittest.TestCase):
 def test_contract(self):
  r=make("division","denominator zero","undefined","p");self.assertEqual(r["type"],"BOUNDARY_CASE")
  self.assertEqual(r["expected_behavior"],"undefined")
  with self.assertRaises(E):make("c","","x","p")
  with self.assertRaises(E):make("c","x","","p")
