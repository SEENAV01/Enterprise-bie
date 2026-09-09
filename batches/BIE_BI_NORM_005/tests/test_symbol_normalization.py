import unittest
from book_intelligence.symbol_normalization import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(normalize("a−b"),"a-b")
  self.assertEqual(normalize("µm"),"μm")
  self.assertEqual(normalize("a×b"),"a×b")
  with self.assertRaises(E):normalize(None)
if __name__=="__main__":unittest.main()
