import unittest
from bie.math_intelligence.delimiters import *
class T(unittest.TestCase):
 def test_valid(self): self.assertTrue(validate_delimiters("(x+[y])").valid)
 def test_mismatch(self): self.assertFalse(validate_delimiters("(]").valid)
 def test_open(self): self.assertEqual(validate_delimiters("(x").expected,")")
 def test_empty(self): self.assertTrue(validate_delimiters("").valid)
if __name__=="__main__":unittest.main()
