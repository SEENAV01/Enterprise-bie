import unittest
from bie.math_intelligence.subscript import *
class T(unittest.TestCase):
 def test_num(self): self.assertEqual(parse_subscript("x₂").index,"2")
 def test_multi(self): self.assertEqual(parse_subscript("a₁₂").index,"12")
 def test_letter(self): self.assertEqual(parse_subscript("vₙ").index,"n")
 def test_none(self): self.assertIsNone(parse_subscript("x"))
if __name__=="__main__":unittest.main()
