
import unittest
from book_intelligence.table_semantics import *
class T(unittest.TestCase):
 def test_ok(self):self.assertEqual(infer(["A","B"],[[1,2]])["columns"]["B"],(2,))
 def test_rows(self):self.assertEqual(infer(["A"],[[1],[2]])["row_count"],2)
 def test_empty(self):
  with self.assertRaises(TableSemanticError):infer([],[])
 def test_dup(self):
  with self.assertRaises(TableSemanticError):infer(["A","A"],[])
 def test_ragged(self):
  with self.assertRaises(TableSemanticError):infer(["A","B"],[[1]])
if __name__=="__main__":unittest.main()
