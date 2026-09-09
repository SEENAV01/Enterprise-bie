import unittest
from app.bie.math_intelligence.simplification import *
class T(unittest.TestCase):
 def test_simple(self): self.assertTrue(validate_simplification("x+0","x",True).valid)
 def test_not_equiv(self): self.assertFalse(validate_simplification("x+1","x",False).valid)
 def test_complexity(self): self.assertGreater(complexity("(x+1)*2"),complexity("x"))
 def test_growth(self): self.assertFalse(validate_simplification("x","x+0",True).valid)
if __name__=="__main__":unittest.main()
