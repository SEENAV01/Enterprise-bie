from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping
import math
from .errors import GameContractError
from .ids import require_id

class ValueType(str,Enum):
    NUMBER='number'; INTEGER='integer'; BOOLEAN='boolean'; STRING='string'; ENUM='enum'

class BinaryOp(str,Enum): ADD='add';SUB='sub';MUL='mul';DIV='div'
class CompareOp(str,Enum): EQ='eq';NE='ne';LT='lt';LE='le';GT='gt';GE='ge'
class BoolOp(str,Enum): AND='and';OR='or'

@dataclass(frozen=True)
class Expr: pass
@dataclass(frozen=True)
class Literal(Expr): value: Any
@dataclass(frozen=True)
class Variable(Expr): name: str
@dataclass(frozen=True)
class Binary(Expr): op: BinaryOp; left: Expr; right: Expr
@dataclass(frozen=True)
class Compare(Expr): op: CompareOp; left: Expr; right: Expr
@dataclass(frozen=True)
class Boolean(Expr): op: BoolOp; values: tuple[Expr,...]
@dataclass(frozen=True)
class Not(Expr): value: Expr

_ALLOWED_LITERAL=(str,int,float,bool,type(None))

def validate_expr(expr: Expr, variables: Mapping[str,ValueType]|None=None, depth=0):
    if depth>32: raise GameContractError('GAME_EXPR_DEPTH')
    variables=variables or {}
    if isinstance(expr,Literal):
        if type(expr.value) not in _ALLOWED_LITERAL: raise GameContractError('GAME_EXPR_LITERAL_TYPE')
        if type(expr.value) is float and not math.isfinite(expr.value):raise GameContractError('GAME_EXPR_NONFINITE')
    elif isinstance(expr,Variable):
        require_id(expr.name,'GAME_EXPR_VARIABLE')
        if variables and expr.name not in variables: raise GameContractError('GAME_EXPR_UNKNOWN_VARIABLE',expr.name)
    elif isinstance(expr,Binary):
        if type(expr.op) is not BinaryOp: raise GameContractError('GAME_EXPR_BINARY_OP')
        validate_expr(expr.left,variables,depth+1);validate_expr(expr.right,variables,depth+1)
    elif isinstance(expr,Compare):
        if type(expr.op) is not CompareOp: raise GameContractError('GAME_EXPR_COMPARE_OP')
        validate_expr(expr.left,variables,depth+1);validate_expr(expr.right,variables,depth+1)
    elif isinstance(expr,Boolean):
        if type(expr.op) is not BoolOp or len(expr.values)<2: raise GameContractError('GAME_EXPR_BOOL')
        for v in expr.values:validate_expr(v,variables,depth+1)
    elif isinstance(expr,Not): validate_expr(expr.value,variables,depth+1)
    else: raise GameContractError('GAME_EXPR_NODE',type(expr).__name__)
    return expr

def evaluate(expr: Expr, state: Mapping[str,Any]):
    validate_expr(expr,{k:ValueType.NUMBER for k in state})
    if isinstance(expr,Literal):return expr.value
    if isinstance(expr,Variable):return state[expr.name]
    if isinstance(expr,Binary):
        a,b=evaluate(expr.left,state),evaluate(expr.right,state)
        if expr.op==BinaryOp.ADD:return a+b
        if expr.op==BinaryOp.SUB:return a-b
        if expr.op==BinaryOp.MUL:return a*b
        if expr.op==BinaryOp.DIV:
            if b==0:raise GameContractError('GAME_EXPR_DIV_ZERO')
            return a/b
    if isinstance(expr,Compare):
        a,b=evaluate(expr.left,state),evaluate(expr.right,state)
        if expr.op==CompareOp.EQ:return a==b
        if expr.op==CompareOp.NE:return a!=b
        try:
            if expr.op==CompareOp.LT:return a<b
            if expr.op==CompareOp.LE:return a<=b
            if expr.op==CompareOp.GT:return a>b
            if expr.op==CompareOp.GE:return a>=b
        except TypeError as exc:raise GameContractError('GAME_EXPR_COMPARABLE_REQUIRED') from exc
    if isinstance(expr,Boolean):
        vals=[bool(evaluate(v,state)) for v in expr.values];return all(vals) if expr.op==BoolOp.AND else any(vals)
    if isinstance(expr,Not):return not bool(evaluate(expr.value,state))
    raise GameContractError('GAME_EXPR_EVAL')
