import unittest
from bie.knowledge_intelligence.equation_claim_link import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(link("e","c","EXPRESSES","p")["role"],"EXPRESSES")
  self.assertEqual(link("e","c","DERIVES","p")["claim_id"],"c")
  with self.assertRaises(E):link("","c","EXPRESSES","p")
  with self.assertRaises(E):link("e","c","BAD","p")
