import unittest
from bie.game_engine.compiler_engine.expression_codegen import compile_expr
from bie.game_engine.expressions import *
class ExprCodegenTests(unittest.TestCase):
 def test_nested_expression(self):self.assertEqual(compile_expr(Boolean(BoolOp.AND,(Compare(CompareOp.GE,Variable('x'),Literal(1)),Not(Compare(CompareOp.EQ,Variable('y'),Literal(0))))),{'x':ValueType.NUMBER,'y':ValueType.NUMBER}),'((Number(state["x"])>=1)&&(!(Number(state["y"])===0)))')
 def test_unknown_variable_fails(self):
  with self.assertRaises(Exception):compile_expr(Variable('missing'),{'x':ValueType.NUMBER})
 def test_literal_string_json_escaped(self):self.assertEqual(compile_expr(Literal('a"b')), '"a\\"b"')
