import unittest
from app.bie.math_intelligence.fractions import *
class T(unittest.TestCase):
 def test_slash(self): self.assertEqual(parse_fraction("a/b").denominator,"b")
 def test_latex(self): self.assertEqual(parse_fraction(r"\\frac{x+1}{2}").numerator,"x+1")
 def test_group(self): self.assertEqual(parse_fraction("(a/b)/c").numerator,"(a/b)")
 def test_none(self): self.assertIsNone(parse_fraction("x"))
if __name__=="__main__":unittest.main()
