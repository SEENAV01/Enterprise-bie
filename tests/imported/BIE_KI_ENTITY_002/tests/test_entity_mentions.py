import unittest
from bie.knowledge_intelligence.entity_mentions import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(mention("e","Newton wrote","p",0,6)["surface"],"Newton")
  self.assertEqual(mention("e","abc","p",0,1)["span"],(0,1))
  with self.assertRaises(E):mention("e","abc","p",2,2)
  with self.assertRaises(E):mention("","abc","p",0,1)
