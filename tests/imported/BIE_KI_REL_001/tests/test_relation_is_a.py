import unittest
from knowledge_intelligence.relation_is_a import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(edge("dog","animal",["a"],.9)["type"],"IS_A")
  with self.assertRaises(E):edge("a","a",["x"],1)
  with self.assertRaises(E):edge("a","b",[],1)
  with self.assertRaises(E):edge("a","b",["x"],2)
if __name__=='__main__':unittest.main()
