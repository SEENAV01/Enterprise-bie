
import unittest
from book_intelligence.page_inventory import *
class T(unittest.TestCase):
 def p(self,i=1):return PageRecord(i,str(i),600,800,True,0)
 def test_ok(self):self.assertEqual(len(validate_pages([self.p()])),1)
 def test_empty(self):
  with self.assertRaises(PageInventoryError):validate_pages([])
 def test_order(self):
  with self.assertRaises(PageInventoryError):validate_pages([self.p(2)])
 def test_dim(self):
  with self.assertRaises(PageInventoryError):validate_pages([PageRecord(1,None,0,1,False,0)])
 def test_images(self):
  with self.assertRaises(PageInventoryError):validate_pages([PageRecord(1,None,1,1,False,-1)])
if __name__=="__main__":unittest.main()
