import unittest
from bie.knowledge_intelligence.condition_claim_link import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(link("k","c","VALID_WHEN",["p"])["role"],"VALID_WHEN")
  self.assertEqual(link("k","c","REQUIRES",["p","p"])["anchors"],("p",))
  with self.assertRaises(E):link("k","c","BAD",["p"])
  with self.assertRaises(E):link("k","c","REQUIRES",[])
