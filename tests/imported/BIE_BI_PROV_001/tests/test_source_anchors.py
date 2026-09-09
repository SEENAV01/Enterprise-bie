import unittest
from bie.document_intelligence.source_anchors import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertTrue(validate(Anchor("a"*64,1,"r",(0,0,1,1))))
  with self.assertRaises(E):validate(Anchor("x",1,"r",(0,0,1,1)))
  with self.assertRaises(E):validate(Anchor("a"*64,0,"r",(0,0,1,1)))
  with self.assertRaises(E):validate(Anchor("a"*64,1,"r",(0,0,2,1)))
if __name__=="__main__":unittest.main()
