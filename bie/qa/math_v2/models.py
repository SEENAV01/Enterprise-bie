"""Immutable, operator-governed mathematics QA scope and content-bound cases."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from ..release_v2.contracts import ContractError,token,integer,choice,tuple_tokens,digest
from ..source_v2.models import Request as SourceRequest,Policy as SourcePolicy,records
from .expression import Expr,rational,SYM
from .algebra import Interval
from .units import unit
VERSION='1.0.0'
KINDS=('formula','derivation','numerical','units')

def optional_id(s,field):
    if type(s) is not str:raise ContractError('INVALID_OPTIONAL_ID',field)
    if s:token(s,field)

def typed(e):
    if type(e) is not Expr:raise ContractError('INVALID_TYPED_MATH_EXPRESSION')

def ids(value,field,minimum=0):tuple_tokens(value,field,minimum,256)

@dataclass(frozen=True,slots=True)
class Equation:
    left:Expr
    right:Expr
    def __post_init__(self):typed(self.left);typed(self.right)

@dataclass(frozen=True,slots=True)
class SymbolSpec:
    name:str
    unit:str
    bounds:tuple[str,...]=()
    def __post_init__(self):
        if type(self.name) is not str or not SYM.fullmatch(self.name):raise ContractError('INVALID_MATH_SYMBOL')
        unit(self.unit)
        if type(self.bounds) is not tuple or len(self.bounds) not in (0,2):raise ContractError('INVALID_SYMBOL_BOUNDS')
        if self.bounds and rational(self.bounds[0])>rational(self.bounds[1]):raise ContractError('REVERSED_SYMBOL_BOUNDS')

@dataclass(frozen=True,slots=True)
class Scope:
    scope_id:str
    symbols:tuple[SymbolSpec,...]
    nonzero:tuple[Expr,...]=()
    def __post_init__(self):
        token(self.scope_id,'scope_id');records(self.symbols,SymbolSpec,'symbols','name')
        if len(self.symbols)>8 or type(self.nonzero) is not tuple or len(self.nonzero)>16:raise ContractError('MATH_SCOPE_LIMIT')
        names={s.name for s in self.symbols}
        for e in self.nonzero:
            typed(e)
            if not e.symbols<=names:raise ContractError('UNDECLARED_CONDITION_SYMBOL')
        if len(set(self.nonzero))!=len(self.nonzero):raise ContractError('DUPLICATE_NONZERO_CONDITION')
    @property
    def interval_bounds(self):return {s.name:Interval(rational(s.bounds[0]),rational(s.bounds[1])) for s in self.symbols if s.bounds}
    @property
    def symbol_units(self):return {s.name:s.unit for s in self.symbols}
    @property
    def conditional(self):return bool(self.nonzero or any(s.bounds for s in self.symbols))

@dataclass(frozen=True,slots=True)
class FormulaReference:
    reference_id:str
    scope_id:str
    equation:Equation
    def __post_init__(self):
        token(self.reference_id,'reference_id');token(self.scope_id,'scope_id')
        if type(self.equation) is not Equation:raise ContractError('INVALID_REFERENCE_EQUATION')

@dataclass(frozen=True,slots=True)
class Binding:
    name:str
    lo:str
    hi:str
    unit:str
    def __post_init__(self):
        if type(self.name) is not str or not SYM.fullmatch(self.name):raise ContractError('INVALID_BINDING_SYMBOL')
        if rational(self.lo)>rational(self.hi):raise ContractError('REVERSED_NUMERICAL_INTERVAL')
        unit(self.unit)
    @property
    def interval(self):return Interval(rational(self.lo),rational(self.hi))

@dataclass(frozen=True,slots=True)
class NumericalReference:
    reference_id:str
    scope_id:str
    expression:Expr
    inputs:tuple[Binding,...]
    output_unit:str
    mode:str='exact_point'
    abs_tolerance:str='0'
    rel_tolerance:str='0'
    decimal_places:int=2
    max_interval_width:str='0'
    def __post_init__(self):
        token(self.reference_id,'reference_id');token(self.scope_id,'scope_id');typed(self.expression)
        records(self.inputs,Binding,'inputs','name');unit(self.output_unit)
        if len(self.inputs)>8:raise ContractError('NUMERICAL_INPUT_LIMIT')
        choice(self.mode,('exact_point','rounded_point','interval'),'numeric.mode')
        a,r,w=map(rational,(self.abs_tolerance,self.rel_tolerance,self.max_interval_width))
        if min(a,r,w)<0 or r>rational('1/100'):raise ContractError('INVALID_NUMERICAL_TOLERANCE')
        integer(self.decimal_places,'decimal_places',0,12)
        if self.mode=='rounded_point' and (a or r):raise ContractError('ROUNDING_TOLERANCE_NOT_ALLOWED')
        if self.mode!='interval' and any(b.lo!=b.hi and b.interval.lo!=b.interval.hi for b in self.inputs):raise ContractError('POINT_REFERENCE_HAS_UNCERTAIN_INPUT')
        if self.mode=='interval' and (a or r):raise ContractError('INTERVAL_TOLERANCE_NOT_ALLOWED')
        if {b.name for b in self.inputs}!=set(self.expression.symbols):raise ContractError('NUMERICAL_INPUT_INVENTORY_MISMATCH')

@dataclass(frozen=True,slots=True)
class Requirement:
    case_id:str
    kind:str
    scope_id:str
    reference_id:str=''
    end_reference_id:str=''
    minimum_steps:int=1
    def __post_init__(self):
        for f in ('case_id','scope_id'):token(getattr(self,f),f)
        choice(self.kind,KINDS,'requirement.kind');optional_id(self.reference_id,'reference_id');optional_id(self.end_reference_id,'end_reference_id')
        integer(self.minimum_steps,'minimum_steps',1,64)
        if self.kind!='units' and not self.reference_id:raise ContractError('REQUIRED_REFERENCE_MISSING')
        if (self.kind=='derivation')!=bool(self.end_reference_id):raise ContractError('END_REFERENCE_SCOPE_MISMATCH')
        if self.kind=='units' and self.reference_id:raise ContractError('UNEXPECTED_UNIT_REFERENCE')

def common_case(case):
    token(case.case_id,'case_id');token(case.scope_id,'scope_id');ids(case.claim_ids,'claim_ids',1);ids(case.condition_claim_ids,'condition_claim_ids')
    if set(case.claim_ids)&set(case.condition_claim_ids):raise ContractError('CONDITION_CONTENT_SPAN_COLLISION')

@dataclass(frozen=True,slots=True)
class FormulaCase:
    case_id:str
    scope_id:str
    reference_id:str
    claim_ids:tuple[str,...]
    condition_claim_ids:tuple[str,...]
    equation:Equation
    def __post_init__(self):
        common_case(self);token(self.reference_id,'reference_id')
        if type(self.equation) is not Equation:raise ContractError('INVALID_FORMULA_EQUATION')

@dataclass(frozen=True,slots=True)
class DerivationStep:
    step_id:str
    claim_ids:tuple[str,...]
    before:Equation
    after:Equation
    rule:str
    operand:Expr
    def __post_init__(self):
        token(self.step_id,'step_id');ids(self.claim_ids,'step.claim_ids',1)
        if type(self.before) is not Equation or type(self.after) is not Equation:raise ContractError('INVALID_DERIVATION_EQUATION')
        choice(self.rule,('rewrite','swap','add_both','subtract_both','multiply_both','divide_both','square_both','differentiate','substitute'),'derivation.rule');typed(self.operand)
        if self.rule in ('rewrite','swap','square_both','differentiate','substitute') and self.operand!=Expr('num','0'):raise ContractError('UNEXPECTED_STEP_OPERAND')

@dataclass(frozen=True,slots=True)
class DerivationCase:
    case_id:str
    scope_id:str
    reference_id:str
    end_reference_id:str
    claim_ids:tuple[str,...]
    condition_claim_ids:tuple[str,...]
    steps:tuple[DerivationStep,...]
    def __post_init__(self):
        common_case(self)
        for f in ('reference_id','end_reference_id'):token(getattr(self,f),f)
        records(self.steps,DerivationStep,'steps','step_id',1)
        if len(self.steps)>64:raise ContractError('DERIVATION_STEP_LIMIT')
        if not set(c for s in self.steps for c in s.claim_ids)<=set(self.claim_ids):raise ContractError('STEP_CLAIM_OUTSIDE_CASE')

@dataclass(frozen=True,slots=True)
class NumericalCase:
    case_id:str
    scope_id:str
    reference_id:str
    claim_ids:tuple[str,...]
    condition_claim_ids:tuple[str,...]
    expression:Expr
    inputs:tuple[Binding,...]
    reported_lo:str
    reported_hi:str
    output_unit:str
    def __post_init__(self):
        common_case(self);token(self.reference_id,'reference_id');typed(self.expression)
        records(self.inputs,Binding,'inputs','name')
        if len(self.inputs)>8 or rational(self.reported_lo)>rational(self.reported_hi):raise ContractError('INVALID_NUMERICAL_CASE')
        unit(self.output_unit)

@dataclass(frozen=True,slots=True)
class Conversion:
    conversion_id:str
    lo:str
    hi:str
    from_unit:str
    to_unit:str
    reported_lo:str
    reported_hi:str
    def __post_init__(self):
        token(self.conversion_id,'conversion_id');unit(self.from_unit);unit(self.to_unit)
        if rational(self.lo)>rational(self.hi) or rational(self.reported_lo)>rational(self.reported_hi):raise ContractError('INVALID_CONVERSION_INTERVAL')

@dataclass(frozen=True,slots=True)
class UnitCase:
    case_id:str
    scope_id:str
    claim_ids:tuple[str,...]
    condition_claim_ids:tuple[str,...]
    equation:Equation
    conversions:tuple[Conversion,...]=()
    def __post_init__(self):
        common_case(self)
        if type(self.equation) is not Equation:raise ContractError('INVALID_UNIT_EQUATION')
        records(self.conversions,Conversion,'conversions','conversion_id')
        if len(self.conversions)>32:raise ContractError('UNIT_CONVERSION_LIMIT')

@dataclass(frozen=True,slots=True)
class MathRequest:
    schema_version:str
    source:SourceRequest
    formulas:tuple[FormulaCase,...]
    derivations:tuple[DerivationCase,...]
    numericals:tuple[NumericalCase,...]
    units:tuple[UnitCase,...]
    def __post_init__(self):
        if self.schema_version!=VERSION or type(self.schema_version) is not str:raise ContractError('UNSUPPORTED_MATH_SCHEMA')
        if type(self.source) is not SourceRequest:raise ContractError('INVALID_MATH_SOURCE')
        allids=['math-scope'];node_total=0
        for field,cls in [('formulas',FormulaCase),('derivations',DerivationCase),('numericals',NumericalCase),('units',UnitCase)]:
            rows=getattr(self,field);records(rows,cls,field,'case_id')
            if len(rows)>64:raise ContractError('MATH_CASE_LIMIT')
            for row in rows:
                allids.append(row.case_id)
                if field=='derivations':allids.extend(s.step_id for s in row.steps)
                if field=='units':allids.extend(c.conversion_id for c in row.conversions)
        if len(set(allids))!=len(allids):raise ContractError('MATH_SUBJECT_COLLISION')
        if sum(len(c.steps) for c in self.derivations)>256:raise ContractError('TOTAL_DERIVATION_LIMIT')
        # Bound aggregate request, not just each expression.
        if len(str(self.to_dict()))>2_000_000:raise ContractError('MATH_REQUEST_RESOURCE_LIMIT')
    def to_dict(self):return asdict(self)
    @property
    def content_digest(self):return digest(self.to_dict())

@dataclass(frozen=True,slots=True)
class MathPolicy:
    policy_id:str
    source:SourcePolicy
    scopes:tuple[Scope,...]
    formula_references:tuple[FormulaReference,...]
    numerical_references:tuple[NumericalReference,...]
    requirements:tuple[Requirement,...]
    minimum_review_confidence_ppm:int=900000
    minimum_independent_assessors:int=1
    max_receipt_age_seconds:int=86400
    def __post_init__(self):
        token(self.policy_id,'policy_id')
        if type(self.source) is not SourcePolicy:raise ContractError('INVALID_MATH_SOURCE_POLICY')
        for field,cls,key in [('scopes',Scope,'scope_id'),('formula_references',FormulaReference,'reference_id'),('numerical_references',NumericalReference,'reference_id'),('requirements',Requirement,'case_id')]:
            records(getattr(self,field),cls,field,key)
            if len(getattr(self,field))>256:raise ContractError('MATH_POLICY_LIMIT')
        if not self.scopes or not self.requirements:raise ContractError('EMPTY_MATH_POLICY')
        scopes={s.scope_id:s for s in self.scopes};refs={r.reference_id:r for r in self.formula_references};nums={r.reference_id:r for r in self.numerical_references}
        if set(refs)&set(nums):raise ContractError('REFERENCE_ID_COLLISION')
        for ref in self.formula_references+self.numerical_references:
            if ref.scope_id not in scopes:raise ContractError('REFERENCE_SCOPE_MISSING')
            symbols=(ref.equation.left.symbols|ref.equation.right.symbols) if type(ref) is FormulaReference else ref.expression.symbols
            if not symbols<=set(scopes[ref.scope_id].symbol_units):raise ContractError('UNDECLARED_REFERENCE_SYMBOL')
        for r in self.requirements:
            if r.scope_id not in scopes:raise ContractError('REQUIREMENT_SCOPE_MISSING')
            if r.kind=='units':continue
            collection=nums if r.kind=='numerical' else refs
            for rid in (r.reference_id,)+( (r.end_reference_id,) if r.kind=='derivation' else ()):
                if rid not in collection or collection[rid].scope_id!=r.scope_id:raise ContractError('REQUIREMENT_REFERENCE_MISMATCH')
        integer(self.minimum_review_confidence_ppm,'minimum_review_confidence_ppm',900000,1000000)
        integer(self.minimum_independent_assessors,'minimum_independent_assessors',1,3)
        integer(self.max_receipt_age_seconds,'max_receipt_age_seconds',1,604800)
    @property
    def content_digest(self):return digest(asdict(self))
