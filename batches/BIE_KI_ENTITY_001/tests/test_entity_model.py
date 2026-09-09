import unittest
from knowledge_intelligence.entity_model import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(make("e","Earth","PLACE",["p"])["kind"],"PLACE")
  self.assertEqual(make("e","electron","SCIENTIFIC_OBJECT",["p"])["anchors"],("p",))
  with self.assertRaises(E):make("","x","OTHER",["p"])
  with self.assertRaises(E):make("e","x","BAD",["p"])
