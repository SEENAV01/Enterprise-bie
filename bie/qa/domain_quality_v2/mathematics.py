"""HARD014: exact polynomial calculus, rational linear algebra and units.

No string eval/sympify, arbitrary CAS or numerical sampling as proof. All operators
consume the inherited bounded typed grammar; unknown profiles return review.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction as Q
from .common import *
from .parser import checked_expression
from ..math_v2.algebra import rational_polynomial,clean,domain_issues,Interval
from ..math_v2.expression import parse as expression_parse

@dataclass(frozen=True)
class MathPolicy(PolicyDigest):
    required_ids: tuple[str,...]
    max_dimension: int=6
    max_cases: int=128
    max_absolute_tolerance: str="0"
    def __post_init__(self):
        require(0<=rational(self.max_absolute_tolerance)<=Q(1,1000000),'MATH_POLICY_TOLERANCE');ids(self.required_ids,'MATH_CASE');integer(self.max_dimension,'matrix_dimension',1,6);integer(self.max_cases,'math_cases',1,128)

def polynomial(s):
    # No division by a variable or cancelled undefined expression in this profile.
    e=expression_parse(s)
    stack=[e]
    while stack:
        x=stack.pop();stack.extend(x.args)
        require(x.op not in ('sin','cos','log','exp','sqrt','abs'),'CALCULUS_NONPOLYNOMIAL')
    n,d=rational_polynomial(e)
    stack=[e]
    while stack:
        x=stack.pop();stack.extend(x.args)
        if x.op=='div':require(not x.args[1].symbols,'CALCULUS_DOMAIN_REQUIRES_REVIEW')
        if x.op=='pow':require(rational(x.args[1].value)>0 or not x.args[0].symbols,'CALCULUS_DOMAIN_REQUIRES_REVIEW')
    require(set(d)<={()} and d.get((),Q(0))!=0,'CALCULUS_NONPOLYNOMIAL')
    require(len(e.symbols)<=4,'CALCULUS_SYMBOL_LIMIT')
    return clean({m:bounded(c/d[()])for m,c in n.items()})

def derivative(p,variable):
    token(variable,'variable');out={}
    for m,c in p.items():
        powers=dict(m);n=powers.get(variable,0)
        if n:
            powers[variable]=n-1;k=tuple(sorted((s,x)for s,x in powers.items()if x));out[k]=bounded(out.get(k,Q(0))+n*c)
    return clean(out)

def definite_integral(p,variable,lo,hi):
    a,b=rational(lo),rational(hi);require(a<=b,'INTEGRAL_BOUND_ORDER');out={}
    for m,c in p.items():
        powers=dict(m);n=powers.pop(variable,0)+1
        k=tuple(sorted(powers.items()));out[k]=bounded(out.get(k,Q(0))+c*bounded(b**n-a**n)/n)
    return clean(out)

def matrix(v,maximum=6):
    require(type(v)is list and 1<=len(v)<=maximum,'MATRIX_ROWS');require(type(v[0])is list and 1<=len(v[0])<=maximum,'MATRIX_COLUMNS')
    require(all(type(row)is list and len(row)==len(v[0])for row in v),'MATRIX_RECTANGULAR')
    return [[rational(x)for x in row]for row in v]

def product(a,b):
    require(len(a[0])==len(b),'MATRIX_PRODUCT_DIMENSION')
    return [[bounded(sum((bounded(a[i][k]*b[k][j])for k in range(len(b))),Q(0)))for j in range(len(b[0]))]for i in range(len(a))]

def solve(a,b):
    n=len(a);require(len(a[0])==n and len(b)==n and len(b[0])==1,'LINEAR_SYSTEM_DIMENSIONS')
    work=[r[:]+[b[i][0]]for i,r in enumerate(a)]
    for j in range(n):
        pivot=next((i for i in range(j,n)if work[i][j]),None);require(pivot is not None,'NONUNIQUE_LINEAR_SYSTEM_REVIEW')
        work[j],work[pivot]=work[pivot],work[j];q=work[j][j];work[j]=[bounded(x/q)for x in work[j]]
        for i in range(n):
            if i!=j:
                q=work[i][j];work[i]=[bounded(x-q*y)for x,y in zip(work[i],work[j])]
    return [[r[-1]]for r in work]

# A closed, explicitly defined conversion vocabulary. Unit context is not guessed.
UNITS={'m':('length',Q(1)),'km':('length',Q(1000)),'cm':('length',Q(1,100)),
       's':('time',Q(1)),'min':('time',Q(60)),'h':('time',Q(3600)),
       'm/s':('speed',Q(1)),'km/h':('speed',Q(5,18)),
       'm3':('volume',Q(1)),'L':('volume',Q(1,1000)),'mL':('volume',Q(1,1000000)),
       'ratio':('dimensionless',Q(1)),'percent':('dimensionless',Q(1,100)),
       'm2':('area',Q(1)),'cm2':('area',Q(1,10000))}

def exact_case(c,policy):
    kind=c.get('kind');base=('case_id','kind')
    if kind in ('derivative','antiderivative'):
        fields(c,(*base,'expression','variable','result'));p=polynomial(c['expression']);q=polynomial(c['result'])
        ok=derivative(p,c['variable'])==q if kind=='derivative'else derivative(q,c['variable'])==p
        return ok,{'proof':'coefficient_identity','arbitrary_constant_family_not_claimed':kind=='antiderivative'}
    if kind=='definite_integral':
        fields(c,(*base,'expression','variable','lower','upper','result'))
        return definite_integral(polynomial(c['expression']),c['variable'],c['lower'],c['upper'])==polynomial(c['result']),{'proof':'exact_polynomial_antiderivative'}
    if kind in ('matrix_product','linear_solve'):
        fields(c,(*base,'a','b','result'));a=matrix(c['a'],policy.max_dimension);b=matrix(c['b'],policy.max_dimension);got=matrix(c['result'],policy.max_dimension)
        want=product(a,b)if kind=='matrix_product'else solve(a,b)
        return want==got,{'expected':[[qtext(x)for x in row]for row in want]}
    if kind in ('dot','cross'):
        fields(c,(*base,'a','b','frame_a','frame_b','result'));require(c['frame_a']==c['frame_b'],'VECTOR_FRAME_MISMATCH');token(c['frame_a'],'frame')
        a=matrix([c['a']],policy.max_dimension)[0];b=matrix([c['b']],policy.max_dimension)[0];require(len(a)==len(b),'VECTOR_DIMENSION')
        if kind=='dot':want=bounded(sum((bounded(x*y)for x,y in zip(a,b)),Q(0)));return want==rational(c['result']),{'expected':qtext(want)}
        require(len(a)==3,'CROSS_REQUIRES_3D');want=[bounded(a[(i+1)%3]*b[(i+2)%3]-a[(i+2)%3]*b[(i+1)%3])for i in range(3)]
        require(type(c['result'])is list and len(c['result'])==3,'CROSS_RESULT')
        return want==[rational(x)for x in c['result']],{'expected':[qtext(x)for x in want]}
    if kind=='units':
        fields(c,(*base,'value','from_unit','to_unit','result','absolute_tolerance'))
        require(c['from_unit']in UNITS and c['to_unit']in UNITS,'UNIT_NOT_IN_REGISTERED_PROFILE')
        d,s=UNITS[c['from_unit']];e,t=UNITS[c['to_unit']];require(d==e,'UNIT_DIMENSION_MISMATCH')
        want=bounded(rational(c['value'])*s/t);tol=rational(c['absolute_tolerance']);require(0<=tol<=rational(policy.max_absolute_tolerance),'PRECISION_TOLERANCE_WEAKENED')
        return abs(rational(c['result'])-want)<=tol,{'expected':qtext(want),'tolerance':qtext(tol)}
    if kind=='roots':
        fields(c,(*base,'expression','variable','roots'));p=polynomial(c['expression']);v=c['variable'];token(v,'root_variable')
        require(all(all(s==v for s,n in m)for m in p),'ROOT_MULTIVARIABLE_REVIEW')
        degree=max((sum(n for s,n in m)for m in p),default=0);require(degree in (1,2),'ROOT_DEGREE_REVIEW')
        coeff=lambda n:p.get(((v,n),)if n else (),Q(0))
        if degree==1:want={bounded(-coeff(0)/coeff(1))}
        else:
            from math import isqrt
            a,b,d=coeff(2),coeff(1),coeff(0);disc=bounded(b*b-4*a*d)
            if disc<0:want=set()
            else:
                x,y=isqrt(disc.numerator),isqrt(disc.denominator);require(x*x==disc.numerator and y*y==disc.denominator,'IRRATIONAL_ROOT_PROFILE_REVIEW')
                want={bounded((-b+Q(x,y))/(2*a)),bounded((-b-Q(x,y))/(2*a))}
        require(type(c['roots'])is list and len(c['roots'])<=2,'ROOT_INVENTORY');got=[rational(x)for x in c['roots']];require(len(got)==len(set(got)),'DUPLICATE_ROOT')
        return set(got)==want,{'complete_real_root_set':[qtext(x)for x in sorted(want)]}
    fields(c,(*base,'description'));text(c['description'],'unsupported_math');raise ContractError('MATH_PROFILE_NOT_SUPPORTED')

def evaluate_math(ref,root,binding,policy):
    data=read_input(root,ref,binding,policy,'BIE-QA-HARD-014',('cases',));cases=items(data['cases'],'MATH_CASES',1,policy.max_cases)
    mapped=unique(cases,'case_id','MATH_DUPLICATE_CASE');require(set(mapped)==set(policy.required_ids),'MATH_CASE_CENSUS')
    findings=[];out={}
    review_codes={'CALCULUS_DOMAIN_REQUIRES_REVIEW','CALCULUS_NONPOLYNOMIAL','NONUNIQUE_LINEAR_SYSTEM_REVIEW','UNIT_NOT_IN_REGISTERED_PROFILE','IRRATIONAL_ROOT_PROFILE_REVIEW','MATH_PROFILE_NOT_SUPPORTED','ROOT_DEGREE_REVIEW','ROOT_MULTIVARIABLE_REVIEW'}
    for cid,c in mapped.items():
        try:
            ok,details=exact_case(c,policy);out[cid]=dict(passed=ok,**details)
            if not ok:findings.append(Finding('MATHEMATICAL_COUNTEREXAMPLE',cid,'BLOCKER'))
        except ContractError as exc:
            if exc.code not in review_codes:raise
            findings.append(Finding(exc.code,cid));out[cid]=dict(status='REVIEW_REQUIRED',reason=exc.code)
    return finish('BIE-QA-HARD-014',binding,findings,(ref,),out)
