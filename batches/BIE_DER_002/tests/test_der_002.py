import unittest
from app.bie.math_intelligence.derivation_chain import *
class T(unittest.TestCase):
 def test_valid(self): self.assertTrue(validate_chain([Step("a","b"),Step("b","c")]).valid)
 def test_break(self): self.assertEqual(validate_chain([Step("a","b"),Step("x","c")]).breaks,(1,))
 def test_ends(self): self.assertEqual(validate_chain([Step("a","z")]).end,"z")
 def test_empty(self): self.assertFalse(validate_chain([]).valid)
if __name__=="__main__":unittest.main()
