"""Exact, bounded rational-polynomial certificates with original-domain checks.

A sampled counterexample disproves a proposed equality. Finite samples NEVER
prove an identity or equivalent solution set. Unsupported proof remains UNKNOWN.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction as Q
from itertools import product
from math import isqrt
from .expression import Expr,num,rational,qtext,bounded,render
from ..release_v2.contracts import ContractError

@dataclass(frozen=True,slots=True)
class Interval:
    lo: Q
    hi: Q
    def __post_init__(self):
        if type(self.lo) is not Q or type(self.hi) is not Q or self.lo>self.hi:raise ContractError('INVALID_INTERVAL')
        bounded(self.lo);bounded(self.hi)
    def text(self):return (qtext(self.lo),qtext(self.hi))
    def contains_zero(self):return self.lo<=0<=self.hi

def interval(e:Expr,values:dict[str,Interval]) -> Interval:
    if e.op=='num':return Interval(rational(e.value),rational(e.value))
    if e.op=='sym':
        if e.value not in values:raise ContractError('UNBOUNDED_OR_MISSING_SYMBOL',e.value)
        return values[e.value]
    a=interval(e.args[0],values)
    if e.op=='neg':return Interval(-a.hi,-a.lo)
    if e.op=='abs':return Interval(Q(0) if a.contains_zero() else min(abs(a.lo),abs(a.hi)),max(abs(a.lo),abs(a.hi)))
    if e.op=='sqrt':
        if a.lo<0:raise ContractError('SQRT_DOMAIN_INVALID')
        scale=10**24
        def edge(q):
            sn,sd=isqrt(q.numerator),isqrt(q.denominator)
            if sn*sn==q.numerator and sd*sd==q.denominator:return Q(sn,sd),Q(sn,sd)
            n=isqrt(q.numerator*scale*scale//q.denominator)
            return Q(n,scale),Q(n,scale) if Q(n,scale)**2==q else Q(n+1,scale)
        return Interval(edge(a.lo)[0],edge(a.hi)[1])
    if e.op in ('sin','cos','log','exp'):raise ContractError('UNSUPPORTED_INTERVAL_FUNCTION',e.op)
    b=interval(e.args[1],values)
    if e.op=='add':return Interval(bounded(a.lo+b.lo),bounded(a.hi+b.hi))
    if e.op=='sub':return Interval(bounded(a.lo-b.hi),bounded(a.hi-b.lo))
    if e.op=='mul':
        vals=[bounded(x*y) for x in (a.lo,a.hi) for y in (b.lo,b.hi)];return Interval(min(vals),max(vals))
    if e.op=='div':
        if b.contains_zero():raise ContractError('DIVISION_INTERVAL_CONTAINS_ZERO')
        vals=[bounded(x/y) for x in (a.lo,a.hi) for y in (b.lo,b.hi)];return Interval(min(vals),max(vals))
    if e.op=='pow':
        n=int(b.lo)
        if n<=0 and a.contains_zero():raise ContractError('ZERO_TO_NONPOSITIVE_POWER')
        if n==0:return Interval(Q(1),Q(1))
        vals=[bounded(a.lo**abs(n)),bounded(a.hi**abs(n))]
        low=Q(0) if n%2==0 and a.contains_zero() else min(vals);high=max(vals)
        return Interval(bounded(1/high),bounded(1/low)) if n<0 else Interval(low,high)
    raise ContractError('UNSUPPORTED_INTERVAL_OPERATOR')

# Polynomial = {sorted ((symbol, power),...): rational coefficient}.
class Budget:
    def __init__(self,limit=50000):self.left=limit
    def spend(self,n=1):
        self.left-=n
        if self.left<0:raise ContractError('POLYNOMIAL_OPERATION_LIMIT')

def clean(p):
    out={m:bounded(c) for m,c in p.items() if c}
    if len(out)>128 or any(sum(n for _,n in m)>32 for m in out):raise ContractError('POLYNOMIAL_SIZE_LIMIT')
    return out

def add(a,b,budget,sign=1):
    budget.spend(len(a)+len(b));c=dict(a)
    for m,q in b.items():c[m]=c.get(m,Q(0))+sign*q
    return clean(c)

def mul(a,b,budget):
    budget.spend(len(a)*len(b));c={}
    for x,q in a.items():
        for y,r in b.items():
            m=dict(x)
            for v,n in y:m[v]=m.get(v,0)+n
            key=tuple(sorted(m.items()));c[key]=bounded(c.get(key,Q(0))+bounded(q*r))
            if len(c)>256:raise ContractError('POLYNOMIAL_SIZE_LIMIT')
    return clean(c)

def power(a,n,budget):
    c={():Q(1)}
    for _ in range(n):c=mul(c,a,budget)
    return c

def rational_polynomial(e:Expr,budget=None):
    b=Budget() if budget is None else budget;b.spend()
    one={():Q(1)}
    if e.op=='num':return clean({():rational(e.value)}),one
    if e.op=='sym':return {((e.value,1),):Q(1)},one
    if e.op in ('sqrt','abs','sin','cos','log','exp'):raise ContractError('UNSUPPORTED_SYMBOLIC_FUNCTION',e.op)
    n,d=rational_polynomial(e.args[0],b)
    if e.op=='neg':return {m:-q for m,q in n.items()},d
    v,w=rational_polynomial(e.args[1],b)
    if e.op=='add':return add(mul(n,w,b),mul(v,d,b),b),mul(d,w,b)
    if e.op=='sub':return add(mul(n,w,b),mul(v,d,b),b,-1),mul(d,w,b)
    if e.op=='mul':return mul(n,v,b),mul(d,w,b)
    if e.op=='div':
        if not v:raise ContractError('IDENTICALLY_ZERO_DENOMINATOR')
        return mul(n,w,b),mul(d,v,b)
    if e.op=='pow':
        exponent=int(rational(e.args[1].value))
        if exponent<=0 and not n:raise ContractError('ZERO_TO_NONPOSITIVE_POWER')
        return (power(d,-exponent,b),power(n,-exponent,b)) if exponent<0 else (power(n,exponent,b),power(d,exponent,b))
    raise ContractError('UNSUPPORTED_POLYNOMIAL_OPERATOR')

def equal_expressions(a,b):
    budget=Budget();n,d=rational_polynomial(a,budget);v,w=rational_polynomial(b,budget)
    return not add(mul(n,w,budget),mul(v,d,budget),budget,-1)

def proportional(a,b):
    if not a or not b:return not a and not b
    if set(a)!=set(b):return False
    m=sorted(a)[0];ratio=a[m]/b[m]
    return ratio!=0 and all(a[t]==ratio*b[t] for t in a)

def known_nonzero(e, bounds, nonzero=()):
    try:
        v=interval(e,bounds)
        if not v.contains_zero():return True
    except ContractError:pass
    for x in nonzero:
        try:
            a,d=rational_polynomial(e);b,f=rational_polynomial(x)
            if proportional(a,b) and proportional(d,f):return True
        except ContractError:pass
    if e.op=='neg':return known_nonzero(e.args[0],bounds,nonzero)
    if e.op in ('mul','div'):return all(known_nonzero(x,bounds,nonzero) for x in e.args)
    if e.op=='pow':return known_nonzero(e.args[0],bounds,nonzero)
    return False

def domain_issues(e,bounds,nonzero=()):
    out=[];stack=[e]
    while stack:
        x=stack.pop();stack.extend(x.args)
        needed=x.args[1] if x.op=='div' else (x.args[0] if x.op=='pow' and rational(x.args[1].value)<=0 else None)
        if needed is not None and not known_nonzero(needed,bounds,nonzero):
            code='NONZERO_DOMAIN_UNPROVEN'
            try:
                v=interval(needed,bounds)
                if v.lo==v.hi==0:code='ZERO_DENOMINATOR_OR_POWER_DOMAIN'
            except ContractError:pass
            out.append((code,render(needed)))
        if x.op=='sqrt':
            try:
                v=interval(x.args[0],bounds)
                if v.lo<0:out.append(('SQRT_DOMAIN_INVALID',render(x)))
            except ContractError:out.append(('SQRT_DOMAIN_UNPROVEN',render(x)))
        if x.op in ('sin','cos','log','exp'):out.append(('UNSUPPORTED_FUNCTION_DOMAIN',render(x)))
    return tuple(sorted(set(out)))

def sample_points(symbols,bounds,nonzero=(),limit=256):
    names=sorted(symbols)
    if len(names)>8:raise ContractError('MATH_SYMBOL_LIMIT')
    options=[]
    for name in names:
        if name in bounds:
            x=bounds[name];values=[x.lo,(x.lo+x.hi)/2,x.hi]+[Q(i) for i in (0,1,-1,2,-2) if x.lo<=i<=x.hi]
        else:values=[Q(i) for i in (0,1,-1,2,-2,3,-3)]
        options.append(tuple(dict.fromkeys(values)))
    for i,values in enumerate(product(*options)):
        if i>=limit:break
        point={name:Interval(x,x) for name,x in zip(names,values)}
        try:
            if all(not interval(x,point).contains_zero() for x in nonzero):yield point
        except ContractError:continue

@dataclass(frozen=True,slots=True)
class Proof:
    status:str
    code:str
    witness:tuple[tuple[str,str],...]=()

def compare_equations(left,right,ref_left,ref_right,bounds,nonzero=()):
    exprs=(left,right,ref_left,ref_right)
    for e in exprs:
        issues=domain_issues(e,bounds,nonzero)
        if issues:return Proof('UNKNOWN',issues[0][0])
    try:
        a,_=rational_polynomial(Expr('sub','',(left,right)))
        b,_=rational_polynomial(Expr('sub','',(ref_left,ref_right)))
        if (a and set(a)=={()}) or (b and set(b)=={()}):return Proof('UNKNOWN','EMPTY_SOLUTION_SET_UNSUPPORTED')
        if proportional(a,b):return Proof('PROVED','EXACT_RATIONAL_ZERO_SET_CERTIFICATE')
    except ContractError as exc:return Proof('UNKNOWN',exc.code)
    names=set().union(*(e.symbols for e in exprs))
    for point in sample_points(names,bounds,nonzero):
        try:
            vals=[interval(e,point) for e in exprs]
            if any(v.lo!=v.hi for v in vals):continue
            if (vals[0].lo==vals[1].lo)!=(vals[2].lo==vals[3].lo):
                return Proof('DISPROVED','EQUATION_COUNTEREXAMPLE',tuple((n,qtext(v.lo)) for n,v in sorted(point.items())))
        except ContractError:continue
    return Proof('UNKNOWN','NONPROPORTIONAL_RESIDUAL_REQUIRES_PROOF')
