import unittest
from bie.knowledge_intelligence.example_decomposition import *
class T(unittest.TestCase):
 def test_contract(self):
  r=decompose("e","Find force",["Given m","Use F=ma"],"10 N");self.assertEqual(len(r["steps"]),2)
  self.assertEqual(r["answer"],"10 N")
  with self.assertRaises(E):decompose("e","",["x"])
  with self.assertRaises(E):decompose("e","x",[])
if __name__=='__main__':unittest.main()
