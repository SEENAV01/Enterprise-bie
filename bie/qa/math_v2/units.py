"""Explicit, immutable unit vocabulary; rational scales and affine temperatures.

Dimensions alone do not establish a physical law. Formula variables are reviewed
canonical-SI quantities, not implicitly interchangeable displayed magnitudes.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction as Q
from types import MappingProxyType
from .expression import parse,Expr,rational,bounded
from .algebra import Interval
from ..release_v2.contracts import ContractError
D0=(0,0,0,0,0,0,0)  # L,M,T,I,Theta,N,J, matching native Dimension.

@dataclass(frozen=True,slots=True)
class Unit:
    dimensions:tuple[int,...]
    scale:Q=Q(1)
    offset:Q=Q(0)
    kind:str='scalar'
    def __post_init__(self):
        if type(self.dimensions) is not tuple or len(self.dimensions)!=7 or any(type(x) is not int or abs(x)>32 for x in self.dimensions):raise ContractError('INVALID_UNIT_DIMENSION')
        if type(self.scale) is not Q or self.scale<=0 or type(self.offset) is not Q:raise ContractError('INVALID_UNIT_SCALE')
        bounded(self.scale);bounded(self.offset)

def _base(i):return tuple(int(j==i) for j in range(7))
_u={'1':Unit(D0),'rad':Unit(D0,kind='angle'),'percent':Unit(D0,Q(1,100))}
for i,s in enumerate(('m','kg','s','A','K','mol','cd')):_u[s]=Unit(_base(i),kind='absolute_temperature' if s=='K' else 'scalar')
for s,base,scale in [('km','m','1000'),('cm','m','1/100'),('mm','m','1/1000'),('um','m','1/1000000'),('g','kg','1/1000'),('min','s','60'),('h','s','3600'),('ms','s','1/1000')]:_u[s]=Unit(_u[base].dimensions,rational(scale))
for s,d in [('Hz',(0,0,-1,0,0,0,0)),('N',(1,1,-2,0,0,0,0)),('J',(2,1,-2,0,0,0,0)),('Pa',(-1,1,-2,0,0,0,0)),('W',(2,1,-3,0,0,0,0)),('C',(0,0,1,1,0,0,0)),('V',(2,1,-3,-1,0,0,0)),('ohm',(2,1,-3,-2,0,0,0))]:_u[s]=Unit(d)
_u['L']=Unit((3,0,0,0,0,0,0),Q(1,1000))
_u['degC']=Unit(_base(4),Q(1),Q(27315,100),'absolute_temperature')
_u['degF']=Unit(_base(4),Q(5,9),Q(45967,180),'absolute_temperature')
for s,scale in [('delta_K',Q(1)),('delta_degC',Q(1)),('delta_degF',Q(5,9))]:_u[s]=Unit(_base(4),scale,kind='temperature_difference')
UNITS=MappingProxyType(_u);del _u

def unit(text:str)->Unit:
    if type(text) is not str or not 1<=len(text)<=160:raise ContractError('INVALID_UNIT_TEXT')
    if text in UNITS:return UNITS[text]
    e=parse(text)
    def visit(e):
        if e.op=='sym':
            if e.value not in UNITS:raise ContractError('UNKNOWN_UNIT',e.value)
            return UNITS[e.value]
        if e.op=='num' and e.value=='1':return UNITS['1']
        if e.op not in ('mul','div','pow'):raise ContractError('UNSUPPORTED_UNIT_SYNTAX')
        a=visit(e.args[0])
        if a.offset:raise ContractError('AFFINE_UNIT_IN_COMPOUND')
        if e.op=='pow':
            p=int(rational(e.args[1].value))
            return Unit(tuple(d*p for d in a.dimensions),bounded(a.scale**p),kind='compound')
        b=visit(e.args[1])
        if b.offset:raise ContractError('AFFINE_UNIT_IN_COMPOUND')
        sign=1 if e.op=='mul' else -1
        return Unit(tuple(x+sign*y for x,y in zip(a.dimensions,b.dimensions)),bounded(a.scale*b.scale**sign),kind='compound')
    return visit(e)

def compatible(a:Unit,b:Unit):
    if a.dimensions!=b.dimensions:return False
    special={'angle','absolute_temperature','temperature_difference'}
    return a.kind==b.kind if a.kind in special or b.kind in special else True

def convert(value:Interval,from_unit:str,to_unit:str)->Interval:
    a,b=unit(from_unit),unit(to_unit)
    if not compatible(a,b):raise ContractError('UNIT_DIMENSION_OR_KIND_MISMATCH')
    lo=bounded(value.lo*a.scale+a.offset);hi=bounded(value.hi*a.scale+a.offset)
    if a.kind=='absolute_temperature' and lo<0:raise ContractError('BELOW_ABSOLUTE_ZERO')
    return Interval(bounded((lo-b.offset)/b.scale),bounded((hi-b.offset)/b.scale))

def to_si(value:Interval,u:str)->Interval:
    a=unit(u);lo=bounded(value.lo*a.scale+a.offset);hi=bounded(value.hi*a.scale+a.offset)
    if a.kind=='absolute_temperature' and lo<0:raise ContractError('BELOW_ABSOLUTE_ZERO')
    return Interval(lo,hi)

def from_si(value:Interval,u:str)->Interval:
    a=unit(u)
    if a.kind=='absolute_temperature' and value.lo<0:raise ContractError('BELOW_ABSOLUTE_ZERO')
    return Interval(bounded((value.lo-a.offset)/a.scale),bounded((value.hi-a.offset)/a.scale))

def dimension(e:Expr,symbol_units:dict[str,str]):
    if e.op=='num':return None if rational(e.value)==0 else D0  # dimensional zero in sums/equations
    if e.op=='sym':
        if e.value not in symbol_units:raise ContractError('UNDECLARED_UNIT_SYMBOL',e.value)
        a=unit(symbol_units[e.value])
        if a.offset:raise ContractError('AFFINE_SYMBOL_REQUIRES_SI_NORMALIZATION')
        return a.dimensions
    a=dimension(e.args[0],symbol_units)
    if e.op in ('neg','abs'):return a
    if e.op=='sqrt':
        if a is None:return None
        if any(d%2 for d in a):raise ContractError('FRACTIONAL_DIMENSION_UNSUPPORTED')
        return tuple(d//2 for d in a)
    if e.op in ('sin','cos','log','exp'):
        if a not in (None,D0):raise ContractError('DIMENSIONAL_FUNCTION_ARGUMENT')
        return D0
    b=dimension(e.args[1],symbol_units)
    if e.op in ('add','sub'):
        if a is None:return b
        if b is None:return a
        if a!=b:raise ContractError('ADDITION_DIMENSION_MISMATCH')
        return a
    if e.op=='pow':
        if a is None:return None
        p=int(rational(e.args[1].value));return tuple(d*p for d in a)
    if a is None or (e.op=='mul' and b is None):return None
    if b is None:raise ContractError('ZERO_DENOMINATOR_DIMENSION')
    sign=1 if e.op=='mul' else -1
    return tuple(x+sign*y for x,y in zip(a,b))

def same_dimensions(left:Expr,right:Expr,symbol_units):
    a,b=dimension(left,symbol_units),dimension(right,symbol_units)
    return a is None or b is None or a==b
