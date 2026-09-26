from __future__ import annotations
from typing import Any,Mapping
from ..errors import GameContractError
from ..expressions import Expr,Literal,Variable,Binary,Compare,Boolean,Not,BinaryOp,CompareOp,BoolOp,ValueType,validate_expr

_NUMERIC={ValueType.NUMBER,ValueType.INTEGER}
def _type_of(v):
    if type(v) is bool:return ValueType.BOOLEAN
    if type(v) is int:return ValueType.INTEGER
    if type(v) is float:return ValueType.NUMBER
    if type(v) is str:return ValueType.STRING
    return None

def evaluate_typed(expr:Expr,state:Mapping[str,Any],type_map:Mapping[str,ValueType]):
    validate_expr(expr,type_map)
    def ev(n):
        if isinstance(n,Literal):return n.value
        if isinstance(n,Variable):
            if n.name not in state:raise GameContractError('GAME_STATE_EXPR_MISSING_VALUE',n.name)
            expected=type_map[n.name];actual=_type_of(state[n.name])
            if expected==ValueType.NUMBER and actual in _NUMERIC:return float(state[n.name])
            if expected!=actual and expected!=ValueType.ENUM:raise GameContractError('GAME_STATE_EXPR_TYPE',n.name)
            return state[n.name]
        if isinstance(n,Binary):
            a,b=ev(n.left),ev(n.right)
            if type(a) not in (int,float) or type(b) not in (int,float) or isinstance(a,bool) or isinstance(b,bool):raise GameContractError('GAME_STATE_EXPR_NUMERIC_REQUIRED')
            if n.op==BinaryOp.ADD:return a+b
            if n.op==BinaryOp.SUB:return a-b
            if n.op==BinaryOp.MUL:return a*b
            if n.op==BinaryOp.DIV:
                if b==0:raise GameContractError('GAME_EXPR_DIV_ZERO')
                return a/b
        if isinstance(n,Compare):
            a,b=ev(n.left),ev(n.right)
            if n.op in {CompareOp.LT,CompareOp.LE,CompareOp.GT,CompareOp.GE}:
                if type(a) not in (int,float,str) or type(b) not in (int,float,str):raise GameContractError('GAME_STATE_EXPR_COMPARABLE_REQUIRED')
            return {CompareOp.EQ:a==b,CompareOp.NE:a!=b,CompareOp.LT:a<b,CompareOp.LE:a<=b,CompareOp.GT:a>b,CompareOp.GE:a>=b}[n.op]
        if isinstance(n,Boolean):
            vals=[ev(x) for x in n.values]
            if any(type(v) is not bool for v in vals):raise GameContractError('GAME_STATE_EXPR_BOOL_REQUIRED')
            return all(vals) if n.op==BoolOp.AND else any(vals)
        if isinstance(n,Not):
            v=ev(n.value)
            if type(v) is not bool:raise GameContractError('GAME_STATE_EXPR_BOOL_REQUIRED')
            return not v
        raise GameContractError('GAME_STATE_EXPR_NODE')
    return ev(expr)
