import unittest
from bie.knowledge_intelligence.concept_granularity import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(classify(0,1,1),"atomic")
  self.assertEqual(classify(2,1,1),"composite")
  self.assertEqual(classify(5,1,1),"umbrella")
  self.assertEqual(classify(0,0,1),"topic")
  with self.assertRaises(E):classify(-1,0,0)
if __name__=='__main__':unittest.main()
