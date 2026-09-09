import unittest
from book_intelligence.unicode_normalization import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(normalize("e\u0301"),"é")
  self.assertEqual(normalize("Ａ","NFKC"),"A")
  with self.assertRaises(E):normalize(1)
  with self.assertRaises(E):normalize("x","BAD")
if __name__=="__main__":unittest.main()
