from __future__ import annotations
import json
from ..expressions import Expr,Literal,Variable,Binary,Compare,Boolean,Not,BinaryOp,CompareOp,BoolOp,ValueType,validate_expr
from .errors import GameCompilerError
_BIN={BinaryOp.ADD:'+',BinaryOp.SUB:'-',BinaryOp.MUL:'*',BinaryOp.DIV:'/'}
_CMP={CompareOp.EQ:'===',CompareOp.NE:'!==',CompareOp.LT:'<',CompareOp.LE:'<=',CompareOp.GT:'>',CompareOp.GE:'>='}
_BOOL={BoolOp.AND:'&&',BoolOp.OR:'||'}

def _kind(expr,variables):
    if isinstance(expr,Literal):
        if type(expr.value) is bool:return 'boolean'
        if type(expr.value) in (int,float):return 'number'
        if type(expr.value) is str:return 'string'
        return 'null'
    if isinstance(expr,Variable):
        t=variables.get(expr.name)
        if t in (ValueType.NUMBER,ValueType.INTEGER):return 'number'
        if t==ValueType.BOOLEAN:return 'boolean'
        if t==ValueType.STRING:return 'string'
        return 'unknown'
    if isinstance(expr,Binary):return 'number'
    return 'boolean'

def _has_division(expr):
    if isinstance(expr,Binary):return expr.op==BinaryOp.DIV or _has_division(expr.left) or _has_division(expr.right)
    if isinstance(expr,Compare):return _has_division(expr.left) or _has_division(expr.right)
    if isinstance(expr,Boolean):return any(_has_division(v) for v in expr.values)
    if isinstance(expr,Not):return _has_division(expr.value)
    return False
def compile_expr(expr:Expr,variables=None)->str:
    validate_expr(expr,variables or {})
    if isinstance(expr,Literal):return json.dumps(expr.value,ensure_ascii=False,separators=(',',':'))
    if isinstance(expr,Variable):
        access=f'state[{json.dumps(expr.name)}]'
        vtype=(variables or {}).get(expr.name)
        if vtype in (ValueType.NUMBER,ValueType.INTEGER):return f'Number({access})'
        if vtype==ValueType.BOOLEAN:return f'Boolean({access})'
        if vtype==ValueType.STRING:return f'String({access})'
        return access
    if isinstance(expr,Binary):
        if any(_kind(v,variables or {}) not in ('number','unknown') for v in (expr.left,expr.right)):
            raise GameCompilerError('GAME_COMP_EXPR_NUMERIC_REQUIRED')
        if expr.op==BinaryOp.DIV and isinstance(expr.right,Literal) and expr.right.value==0:raise GameCompilerError('GAME_COMP_EXPR_DIV_ZERO')
        left,right=compile_expr(expr.left,variables),compile_expr(expr.right,variables)
        if expr.op==BinaryOp.DIV:
            return '(()=>{const numerator='+left+';const denominator='+right+';if(denominator===0)throw new Error("GAME_EXPR_DIV_ZERO");return numerator/denominator;})()'
        # Token separation is required for subtraction of a negative literal.
        return '('+left+' '+_BIN[expr.op]+' '+right+')'
    if isinstance(expr,Compare):
        left,right=compile_expr(expr.left,variables),compile_expr(expr.right,variables)
        a,b=_kind(expr.left,variables or {}),_kind(expr.right,variables or {})
        if expr.op in (CompareOp.EQ,CompareOp.NE) and {a,b}=={'boolean','number'}:
            if a=='boolean':left='Number('+left+')'
            if b=='boolean':right='Number('+right+')'
        return '('+left+_CMP[expr.op]+right+')'
    if isinstance(expr,Boolean):
        values=[compile_expr(x,variables) for x in expr.values]
        # The authoritative evaluator evaluates every operand, including errors.
        if any(_has_division(x) for x in expr.values):
            return '['+','.join(values)+'].'+('every' if expr.op==BoolOp.AND else 'some')+'(value=>value)'
        return '('+_BOOL[expr.op].join(values)+')'
    if isinstance(expr,Not):return '(!'+compile_expr(expr.value,variables)+')'
    raise GameCompilerError('GAME_COMP_EXPR_NODE')
