import unittest
from book_intelligence.block_provenance import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertTrue(validate("b",("a",),"ocr"))
  with self.assertRaises(E):validate("b",(),"ocr")
  with self.assertRaises(E):validate("b",("a","a"),"ocr")
  with self.assertRaises(E):validate("b",("a",),"guess")
if __name__=="__main__":unittest.main()
