import unittest
from app.bie.math_intelligence.expression_ast import *
class T(unittest.TestCase):
 def test_add(self): self.assertEqual(parse_expression(["a","+","b"]).value,"+")
 def test_mul(self): self.assertEqual(parse_expression(["a","*","b"]).kind,"binary")
 def test_atom(self): self.assertEqual(parse_expression(["x"]).kind,"atom")
 def test_empty(self):
  with self.assertRaises(ValueError): parse_expression([])
if __name__=="__main__":unittest.main()
