from __future__ import annotations
import json
from ..expressions import Expr,Literal,Variable,Binary,Compare,Boolean,Not,BinaryOp,CompareOp,BoolOp,ValueType,validate_expr
from .errors import GameCompilerError
_BIN={BinaryOp.ADD:'+',BinaryOp.SUB:'-',BinaryOp.MUL:'*',BinaryOp.DIV:'/'}
_CMP={CompareOp.EQ:'===',CompareOp.NE:'!==',CompareOp.LT:'<',CompareOp.LE:'<=',CompareOp.GT:'>',CompareOp.GE:'>='}
_BOOL={BoolOp.AND:'&&',BoolOp.OR:'||'}
def compile_expr(expr:Expr,variables=None)->str:
    validate_expr(expr,variables or {})
    if isinstance(expr,Literal):return json.dumps(expr.value,ensure_ascii=False,separators=(',',':'))
    if isinstance(expr,Variable):
        access=f'state[{json.dumps(expr.name)}]'
        vtype=(variables or {}).get(expr.name)
        if vtype in (ValueType.NUMBER,ValueType.INTEGER):return f'Number({access})'
        if vtype==ValueType.BOOLEAN:return f'Boolean({access})'
        if vtype in (ValueType.STRING,ValueType.ENUM):return f'String({access})'
        return access
    if isinstance(expr,Binary):
        if expr.op==BinaryOp.DIV and isinstance(expr.right,Literal) and expr.right.value==0:raise GameCompilerError('GAME_COMP_EXPR_DIV_ZERO')
        return '('+compile_expr(expr.left,variables)+_BIN[expr.op]+compile_expr(expr.right,variables)+')'
    if isinstance(expr,Compare):return '('+compile_expr(expr.left,variables)+_CMP[expr.op]+compile_expr(expr.right,variables)+')'
    if isinstance(expr,Boolean):return '('+_BOOL[expr.op].join(compile_expr(x,variables) for x in expr.values)+')'
    if isinstance(expr,Not):return '(!'+compile_expr(expr.value,variables)+')'
    raise GameCompilerError('GAME_COMP_EXPR_NODE')
