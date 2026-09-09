
import unittest
from book_intelligence.multicolumn_layout import *
class T(unittest.TestCase):
 def test_two(self):
  r=[{"id":"a","kind":"text","box":(0,0,40,10)},{"id":"b","kind":"text","box":(60,0,100,10)}]
  self.assertEqual(len(detect_columns(r,100,.1)),2)
 def test_one(self):
  r=[{"id":"a","kind":"text","box":(0,0,45,10)},{"id":"b","kind":"text","box":(47,20,90,30)}]
  self.assertEqual(len(detect_columns(r,100,.1)),1)
 def test_ignore(self):self.assertEqual(detect_columns([{"id":"f","kind":"figure","box":(0,0,10,10)}],100),())
 def test_page(self):
  with self.assertRaises(ColumnError):detect_columns([],0)
 def test_box(self):
  with self.assertRaises(ColumnError):detect_columns([{"id":"a","kind":"text","box":(20,0,10,1)}],100)
if __name__=="__main__":unittest.main()
