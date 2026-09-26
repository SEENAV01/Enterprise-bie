import unittest
from bie.game_engine.expressions import *
from bie.game_engine.errors import GameContractError
from bie.game_engine.state_engine.expression_runtime import evaluate_typed

class ExpressionRuntimeTests(unittest.TestCase):
 def setUp(self):self.s={'x':2.0,'n':2,'flag':True,'name':'a'};self.t={'x':ValueType.NUMBER,'n':ValueType.INTEGER,'flag':ValueType.BOOLEAN,'name':ValueType.STRING}
 def test_numeric_add(self):self.assertEqual(evaluate_typed(Binary(BinaryOp.ADD,Variable('x'),Literal(1)),self.s,self.t),3.0)
 def test_integer_compare(self):self.assertTrue(evaluate_typed(Compare(CompareOp.EQ,Variable('n'),Literal(2)),self.s,self.t))
 def test_boolean(self):self.assertTrue(evaluate_typed(Boolean(BoolOp.AND,(Variable('flag'),Compare(CompareOp.GT,Variable('x'),Literal(1)))),self.s,self.t))
 def test_not(self):self.assertFalse(evaluate_typed(Not(Variable('flag')),self.s,self.t))
 def test_string_equality(self):self.assertTrue(evaluate_typed(Compare(CompareOp.EQ,Variable('name'),Literal('a')),self.s,self.t))
 def test_unknown_variable(self):
  with self.assertRaises(GameContractError):evaluate_typed(Variable('missing'),self.s,self.t)
 def test_div_zero(self):
  with self.assertRaisesRegex(GameContractError,'GAME_EXPR_DIV_ZERO'):evaluate_typed(Binary(BinaryOp.DIV,Literal(1),Literal(0)),self.s,self.t)
 def test_numeric_operator_rejects_string(self):
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_EXPR_NUMERIC_REQUIRED'):evaluate_typed(Binary(BinaryOp.ADD,Variable('name'),Literal('x')),self.s,self.t)
 def test_bool_operator_requires_bool(self):
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_EXPR_BOOL_REQUIRED'):evaluate_typed(Boolean(BoolOp.AND,(Variable('flag'),Variable('x'))),self.s,self.t)
