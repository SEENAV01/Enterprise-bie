
import unittest
from book_intelligence.layout_segmentation import *
class T(unittest.TestCase):
 def r(self):return Region("r","text",(0,0,1,1),.9)
 def test_ok(self):self.assertEqual(len(normalize([self.r()])),1)
 def test_kind(self):
  with self.assertRaises(LayoutError):normalize([Region("r","x",(0,0,1,1),1)])
 def test_dup(self):
  with self.assertRaises(LayoutError):normalize([self.r(),self.r()])
 def test_box(self):
  with self.assertRaises(LayoutError):normalize([Region("r","text",(1,0,0,1),1)])
 def test_conf(self):
  with self.assertRaises(LayoutError):normalize([Region("r","text",(0,0,1,1),2)])
if __name__=="__main__":unittest.main()
