"""Bounded expression grammar. No eval, exec, sympify or Python AST execution.

All constants are exact rationals. Operators are explicit; there is no implicit
multiplication, LaTeX normalization, unit guessing or Unicode symbol folding.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from fractions import Fraction
import re
from ..release_v2.contracts import ContractError
NUM = re.compile(r'[+-]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z')
FRAC = re.compile(r'([+-]?[0-9]+)/([1-9][0-9]*)\Z')
SYM = re.compile(r'[A-Za-z][A-Za-z0-9_]{0,47}\Z')
LEX = re.compile(r'\s*(?:(\d+(?:\.\d+)?|\.\d+)([eE][+-]?\d+)?|([A-Za-z][A-Za-z0-9_]*)|(\*\*|[+*/^(),-]))')
MAX_BITS=2048
MAX_NODES=128
MAX_DEPTH=24
FUNCTIONS=('sqrt','abs','sin','cos','log','exp')

def bounded(q: Fraction) -> Fraction:
    if q.numerator.bit_length()>MAX_BITS or q.denominator.bit_length()>MAX_BITS:
        raise ContractError('MATH_INTEGER_RESOURCE_LIMIT')
    return q

def rational(s: str) -> Fraction:
    if type(s) is not str or not 1<=len(s)<=160:
        raise ContractError('INVALID_RATIONAL')
    m=FRAC.fullmatch(s)
    if m:
        return bounded(Fraction(int(m[1]),int(m[2])))
    if not NUM.fullmatch(s): raise ContractError('INVALID_RATIONAL')
    if 'e' in s.lower() and abs(int(s.lower().split('e')[1]))>128:
        raise ContractError('MATH_EXPONENT_RESOURCE_LIMIT')
    return bounded(Fraction(s))

def qtext(q: Fraction) -> str:
    q=bounded(q)
    return str(q.numerator) if q.denominator==1 else f'{q.numerator}/{q.denominator}'

@dataclass(frozen=True,slots=True)
class Expr:
    op: str
    value: str = ''
    args: tuple['Expr',...] = ()
    def __post_init__(self):
        if type(self.op) is not str or type(self.value) is not str or type(self.args) is not tuple:
            raise ContractError('INVALID_MATH_EXPRESSION')
        counts={'num':0,'sym':0,'neg':1,'add':2,'sub':2,'mul':2,'div':2,'pow':2,**{f:1 for f in FUNCTIONS}}
        if self.op not in counts or len(self.args)!=counts[self.op] or any(type(a) is not Expr for a in self.args):
            raise ContractError('INVALID_MATH_OPERATOR_ARITY')
        if self.op=='num':
            q=rational(self.value)
            if qtext(q)!=self.value: raise ContractError('NONCANONICAL_RATIONAL')
        elif self.op=='sym':
            if not SYM.fullmatch(self.value) or self.value in FUNCTIONS: raise ContractError('INVALID_MATH_SYMBOL')
        elif self.value:raise ContractError('UNEXPECTED_MATH_VALUE')
        if self.op=='pow':
            e=self.args[1]
            if e.op!='num' or rational(e.value).denominator!=1 or abs(rational(e.value))>8:
                raise ContractError('UNSUPPORTED_MATH_POWER')
        stack=[(self,1)];n=0
        while stack:
            x,d=stack.pop();n+=1
            if n>MAX_NODES or d>MAX_DEPTH:raise ContractError('EXPRESSION_RESOURCE_LIMIT')
            stack.extend((a,d+1) for a in x.args)
    @property
    def symbols(self):
        out=set();stack=[self]
        while stack:
            x=stack.pop()
            if x.op=='sym':out.add(x.value)
            stack.extend(x.args)
        return frozenset(out)
    def to_dict(self):return asdict(self)

def num(v: str|int):
    if type(v) not in (str,int):raise ContractError('INVALID_RATIONAL')
    return Expr('num',qtext(rational(str(v))))

def symbol(s):return Expr('sym',s)

def parse(text: str) -> Expr:
    if type(text) is not str or not text.strip() or len(text)>2048:raise ContractError('INVALID_MATH_TEXT')
    text=text.strip();tokens=[];pos=0
    while pos<len(text):
        m=LEX.match(text,pos)
        if not m:raise ContractError('UNSUPPORTED_MATH_SYNTAX')
        tokens.append((m[1]+(m[2] or '')) if m[1] else (m[3] or m[4]));pos=m.end()
        if len(tokens)>256:raise ContractError('MATH_TOKEN_LIMIT')
    index=0
    def expression(bp=0,depth=1):
        nonlocal index
        if depth>MAX_DEPTH or index>=len(tokens):raise ContractError('MATH_PARSE_LIMIT_OR_OPERAND_MISSING')
        t=tokens[index];index+=1
        if t in ('+','-'):
            a=expression(25,depth+1);left=a if t=='+' else Expr('neg','',(a,))
        elif t=='(':
            left=expression(0,depth+1)
            if index>=len(tokens) or tokens[index]!=')':raise ContractError('UNBALANCED_MATH_PARENTHESES')
            index+=1
        elif t in FUNCTIONS:
            if index>=len(tokens) or tokens[index]!='(':raise ContractError('FUNCTION_PARENTHESES_REQUIRED')
            index+=1;a=expression(0,depth+1)
            if index>=len(tokens) or tokens[index]!=')':raise ContractError('FUNCTION_ARITY_OR_PARENTHESES')
            index+=1;left=Expr(t,'',(a,))
        elif SYM.fullmatch(t):left=symbol(t)
        else:left=num(t)
        powers={'+':10,'-':10,'*':20,'/':20,'^':30,'**':30}
        ops={'+':'add','-':'sub','*':'mul','/':'div','^':'pow','**':'pow'}
        while index<len(tokens) and tokens[index] in powers and powers[tokens[index]]>=bp:
            t=tokens[index];index+=1;p=powers[t]
            right=expression(p if t in ('^','**') else p+1,depth+1)
            if ops[t]=='pow' and right.op=='neg' and right.args[0].op=='num':right=num(qtext(-rational(right.args[0].value)))
            left=Expr(ops[t],'',(left,right))
        return left
    result=expression()
    if index!=len(tokens):raise ContractError('UNCONSUMED_MATH_TOKENS')
    return result

def render(e:Expr)->str:
    if e.op in ('num','sym'):return e.value
    if e.op=='neg':return f'(-{render(e.args[0])})'
    if e.op in FUNCTIONS:return f'{e.op}({render(e.args[0])})'
    return f'({render(e.args[0])}{dict(add="+",sub="-",mul="*",div="/",pow="^")[e.op]}{render(e.args[1])})'
