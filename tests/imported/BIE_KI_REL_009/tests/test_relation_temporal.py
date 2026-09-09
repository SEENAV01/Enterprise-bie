import unittest
from bie.knowledge_intelligence.relation_temporal import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(edge("event1","event2",["p"],.9)["type"],"TEMPORALLY_PRECEDES")
  with self.assertRaises(E):edge("x","x",["p"],1)
  with self.assertRaises(E):edge("x","y",[],1)
  with self.assertRaises(E):edge("x","y",["p"],2)
if __name__=='__main__':unittest.main()
