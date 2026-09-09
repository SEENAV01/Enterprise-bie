
import unittest
from book_intelligence.reading_order import *
class T(unittest.TestCase):
 def test_ok(self):self.assertEqual(validate_order(["a","b"],["a","b"]),("a","b"))
 def test_edges(self):self.assertEqual(edges(("a","b","c")),(("a","b"),("b","c")))
 def test_missing(self):
  with self.assertRaises(ReadingOrderError):validate_order(["a","b"],["a"])
 def test_dup(self):
  with self.assertRaises(ReadingOrderError):validate_order(["a","b"],["a","a"])
 def test_extra(self):
  with self.assertRaises(ReadingOrderError):validate_order(["a"],["a","b"])
if __name__=="__main__":unittest.main()
