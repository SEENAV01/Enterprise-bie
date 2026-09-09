
import unittest
from book_intelligence.page_mapping import *
class T(unittest.TestCase):
 def a(self):return Anchor("s1",1,"r1",(0,0,1,1))
 def test_ok(self):self.assertEqual(len(validate([self.a()],1)),1)
 def test_page(self):
  with self.assertRaises(PageMapError):validate([Anchor("s",2,"r",(0,0,1,1))],1)
 def test_dup(self):
  with self.assertRaises(PageMapError):validate([self.a(),self.a()],1)
 def test_box(self):
  with self.assertRaises(PageMapError):validate([Anchor("s",1,"r",(0,0,2,1))],1)
 def test_count(self):
  with self.assertRaises(PageMapError):validate([],0)
if __name__=="__main__":unittest.main()
