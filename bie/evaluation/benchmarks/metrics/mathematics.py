"""METRIC-005: unit-aware quantities and exact bounded algebra with domains.

Rational functions are encoded as coefficients and declared rational denominator
roots, never Python/sympy expressions. Equality preserves domain exclusions.
"""
from __future__ import annotations
from fractions import Fraction
from ..models import BenchmarkError,ident
from ..domains.structured import amount,choice,record,sequence
from .common import indexed,no_extras,unit,weight
UNITS={'1':('dimensionless',Fraction(1),Fraction(0)),
       'm':('length',Fraction(1),Fraction(0)),'cm':('length',Fraction(1,100),Fraction(0)),
       'mm':('length',Fraction(1,1000),Fraction(0)),'km':('length',Fraction(1000),Fraction(0)),
       's':('time',Fraction(1),Fraction(0)),'min':('time',Fraction(60),Fraction(0)),
       'kg':('mass',Fraction(1),Fraction(0)),'g':('mass',Fraction(1,1000),Fraction(0)),
       'N':('force',Fraction(1),Fraction(0)),'kN':('force',Fraction(1000),Fraction(0)),
       'J':('energy',Fraction(1),Fraction(0)),'kJ':('energy',Fraction(1000),Fraction(0)),
       'K':('temperature',Fraction(1),Fraction(0)),
       'degC':('temperature',Fraction(1),Fraction(27315,100))}

def quantity(value):
    record(value, {'value','unit'});u=choice(value['unit'],UNITS);dim,scale,offset=UNITS[u]
    value=amount(value['value'],signed=True)*scale+offset
    if dim=='temperature' and value<0:raise BenchmarkError('BELOW_ABSOLUTE_ZERO')
    return dim,value

def coeffs(value):
    c=[amount(v,signed=True,maximum=10**6) for v in sequence(value,lower=1,upper=9)]
    while len(c)>1 and c[-1]==0:c.pop()
    return c

def mul(a,b):
    out=[Fraction(0)]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):out[i+j]+=x*y
    while len(out)>1 and not out[-1]:out.pop()
    return out

def rational_function(value):
    record(value, {'numerator','denominator_roots','excluded_values'})
    num=coeffs(value['numerator']);roots=[amount(v,signed=True,maximum=10**6) for v in sequence(value['denominator_roots'],lower=0,upper=8)]
    exclusions=[amount(v,signed=True,maximum=10**6) for v in sequence(value['excluded_values'],lower=0,upper=16)]
    if len(set(exclusions))!=len(exclusions):raise BenchmarkError('DUPLICATE_DOMAIN_EXCLUSION')
    if not set(roots)<=set(exclusions):raise BenchmarkError('DENOMINATOR_ROOT_NOT_EXCLUDED')
    den=[Fraction(1)]
    for root in roots:den=mul(den,[-root,Fraction(1)])
    return num,den,set(exclusions)

def measure(reference,candidate,artifacts):
    record(reference, {'checks'});record(candidate, {'checks'})
    refs=indexed(reference['checks'],{'id','weight','kind','expected','absolute_tolerance','relative_tolerance'},lower=1)
    acts=indexed(candidate['checks'],{'id','value'});no_extras(acts,refs);units=[]
    for key,row in sorted(refs.items()):
        w=weight(row);kind=choice(row['kind'],{'quantity','polynomial','rational_function'})
        atol=amount(row['absolute_tolerance'],maximum=1000000);rtol=amount(row['relative_tolerance'],maximum=1)
        if rtol>Fraction(1,100):raise BenchmarkError('TOLERANCE_OUT_OF_PROFILE')
        if kind!='quantity' and (atol or rtol):raise BenchmarkError('EXACT_ALGEBRA_TOLERANCE_REQUIRED')
        parser=quantity if kind=='quantity' else coeffs if kind=='polynomial' else rational_function
        expected=parser(row['expected']);a=acts.get(key);reasons=[]
        if a is None:reasons=['MISSING_MATH_CHECK']
        else:
            actual=parser(a['value'])
            if kind=='quantity':
                if actual[0]!=expected[0]:reasons=['DIMENSION_MISMATCH']
                elif abs(actual[1]-expected[1])>max(atol,rtol*abs(expected[1])):reasons=['NUMERIC_MISMATCH']
            elif kind=='polynomial':
                if actual!=expected:reasons=['POLYNOMIAL_IDENTITY_MISMATCH']
            else:
                if mul(actual[0],expected[1])!=mul(expected[0],actual[1]):reasons.append('RATIONAL_IDENTITY_MISMATCH')
                if actual[2]!=expected[2]:reasons.append('DOMAIN_EXCLUSIONS_MISMATCH')
        units.append(unit(key,w,0 if reasons else 1,reasons))
    return units,[],{'assessment_scope':'BOUNDED_EXACT_ALGEBRA_AND_WHITELIST_UNITS','unrestricted_symbolic_math':False}
