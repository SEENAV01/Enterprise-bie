import unittest
from app.bie.math_intelligence.superscript import *
class T(unittest.TestCase):
 def test_square(self): self.assertEqual(parse_superscript("x²").exponent,"2")
 def test_negative(self): self.assertEqual(parse_superscript("m⁻²").exponent,"-2")
 def test_base(self): self.assertEqual(parse_superscript("10³").base,"10")
 def test_none(self): self.assertIsNone(parse_superscript("x"))
if __name__=="__main__":unittest.main()
