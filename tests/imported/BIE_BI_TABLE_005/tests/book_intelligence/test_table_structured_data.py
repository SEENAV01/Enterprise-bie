
import unittest
from book_intelligence.table_structured_data import *
class T(unittest.TestCase):
 def test_hash(self):self.assertEqual(len(canonicalize("t",["A"],[[1]],"p1:r1")[1]),64)
 def test_stable(self):self.assertEqual(canonicalize("t",["A"],[[1]],"a")[1],canonicalize("t",["A"],[[1]],"a")[1])
 def test_shape(self):
  with self.assertRaises(StructuredTableError):canonicalize("t",["A","B"],[[1]],"a")
 def test_required(self):
  with self.assertRaises(StructuredTableError):canonicalize("",["A"],[],"a")
 def test_anchor(self):
  with self.assertRaises(StructuredTableError):canonicalize("t",["A"],[],"")
if __name__=="__main__":unittest.main()
