import unittest
from app.bie.math_intelligence.vectors import *
class T(unittest.TestCase):
 def test_latex(self): self.assertEqual(parse_vector(r"\\vec{v}").symbol,"v")
 def test_components(self): self.assertEqual(parse_vector("<1,2,3>").components,("1","2","3"))
 def test_tuple(self): self.assertEqual(parse_vector("(x,y)").notation,"components")
 def test_none(self): self.assertIsNone(parse_vector("v"))
if __name__=="__main__":unittest.main()
