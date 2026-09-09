import unittest
from bie.knowledge_intelligence.entity_concept_link import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(link("earth","planet","INSTANCE_OF",["p"],1)["relation"],"INSTANCE_OF")
  self.assertEqual(link("n","law","DISCOVERED_BY",["p"],.9)["confidence"],.9)
  with self.assertRaises(E):link("e","c","BAD",["p"],1)
  with self.assertRaises(E):link("e","c","INSTANCE_OF",[],1)
