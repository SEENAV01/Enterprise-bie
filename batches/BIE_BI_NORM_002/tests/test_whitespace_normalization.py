import unittest
from book_intelligence.whitespace_normalization import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(normalize(" a   b "),"a b")
  self.assertEqual(normalize("a\n b"),"a\nb")
  self.assertEqual(normalize("a\n b",False),"a b")
  with self.assertRaises(E):normalize(None)
if __name__=="__main__":unittest.main()
