import unittest
from app.bie.math_intelligence.radicals import *
class T(unittest.TestCase):
 def test_sqrt(self): self.assertEqual(parse_radical("√x").index,2)
 def test_cube(self): self.assertEqual(parse_radical("∛8").index,3)
 def test_latex(self): self.assertEqual(parse_radical(r"\\sqrt[4]{x}").index,4)
 def test_none(self): self.assertIsNone(parse_radical("x"))
if __name__=="__main__":unittest.main()
