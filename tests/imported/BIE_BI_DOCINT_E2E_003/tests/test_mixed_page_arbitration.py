import unittest
from bie.document_intelligence.mixed_page_arbitration import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(choose(.95,.8),"NATIVE")
  self.assertEqual(choose(.7,.9),"OCR")
  self.assertEqual(choose(.95,.8,has_math=True),"HYBRID")
  self.assertEqual(choose(.5,.5),"REVIEW")
  with self.assertRaises(E):choose(2,.5)
if __name__=='__main__':unittest.main()
