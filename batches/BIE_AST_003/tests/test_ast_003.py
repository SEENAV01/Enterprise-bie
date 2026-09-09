import unittest
from app.bie.math_intelligence.ast_validation import *
class T(unittest.TestCase):
 def test_valid(self): self.assertTrue(validate_tokens(["x","+","1"]).valid)
 def test_lead(self): self.assertIn("leading_binary_operator",validate_tokens(["+","x"]).errors)
 def test_adjacent(self): self.assertIn("adjacent_binary_operators",validate_tokens(["x","+","*","y"]).errors)
 def test_paren(self): self.assertFalse(validate_tokens(["(","x"]).valid)
if __name__=="__main__":unittest.main()
