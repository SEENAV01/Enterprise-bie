import unittest
from dataclasses import replace
from bie.game_engine.errors import GameContractError
from bie.game_engine.expressions import *
class T(unittest.TestCase):
 def test_arithmetic(self):self.assertEqual(evaluate(Binary(BinaryOp.ADD,Variable('x'),Literal(2)),{'x':3}),5)
 def test_compare(self):self.assertTrue(evaluate(Compare(CompareOp.GT,Variable('x'),Literal(2)),{'x':3}))
 def test_boolean(self):self.assertTrue(evaluate(Boolean(BoolOp.AND,(Literal(True),Literal(True))),{}))
 def test_not(self):self.assertFalse(evaluate(Not(Literal(True)),{}))
 def test_div_zero(self):
  with self.assertRaises(GameContractError):evaluate(Binary(BinaryOp.DIV,Literal(1),Literal(0)),{})
 def test_unknown_var(self):
  with self.assertRaises(GameContractError):validate_expr(Variable('y'),{'x':ValueType.NUMBER})
 def test_unsupported_node(self):
  with self.assertRaises(GameContractError):validate_expr(object())
 def test_depth(self):
  e=Literal(1)
  for _ in range(34):e=Not(e)
  with self.assertRaises(GameContractError):validate_expr(e)
