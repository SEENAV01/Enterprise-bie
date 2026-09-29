"""Exact recomputation, conservative interval enclosures, explicit rounding."""
from fractions import Fraction as Q
import re
from .expression import rational,qtext
from .algebra import interval,Interval,equal_expressions,Proof
from .units import unit,compatible,to_si,from_si,dimension
from ..release_v2.contracts import ContractError

def rounded_text(q:Q,places:int)->str:
    # Integer arithmetic, round-half-to-even; Decimal's ambient context is irrelevant.
    sign='-' if q<0 else '';x=abs(q)*10**places;n,r=divmod(x.numerator,x.denominator)
    if 2*r>x.denominator or (2*r==x.denominator and n%2):n+=1
    if n==0:sign=''
    digits=str(n).zfill(places+1)
    return sign+(digits if not places else digits[:-places]+'.'+digits[-places:])

def check_numeric(case,reference,scope):
    if {b.name for b in case.inputs}!={b.name for b in reference.inputs}:return Proof('DISPROVED','NUMERICAL_BINDING_INVENTORY_MISMATCH'),None
    if case.output_unit!=reference.output_unit:return Proof('DISPROVED','NUMERICAL_OUTPUT_UNIT_MISMATCH'),None
    actual={b.name:b for b in case.inputs};values={}
    try:
        if case.expression!=reference.expression and not equal_expressions(case.expression,reference.expression):return Proof('UNKNOWN','NUMERICAL_EXPRESSION_MAPPING_NOT_EQUIVALENT'),None
        for expected in reference.inputs:
            b=actual[expected.name]
            if not compatible(unit(b.unit),unit(expected.unit)):return Proof('DISPROVED','NUMERICAL_INPUT_UNIT_MISMATCH'),None
            a,e=to_si(b.interval,b.unit),to_si(expected.interval,expected.unit)
            if a!=e:return Proof('DISPROVED','NUMERICAL_INPUT_VALUE_MISMATCH'),None
            symbol_unit=unit(scope.symbol_units[b.name])
            if not compatible(unit(b.unit),symbol_unit):return Proof('DISPROVED','NUMERICAL_SYMBOL_UNIT_MISMATCH'),None
            if b.name in scope.interval_bounds:
                bounds=scope.interval_bounds[b.name]
                if a.lo<bounds.lo or a.hi>bounds.hi:return Proof('DISPROVED','NUMERICAL_INPUT_OUTSIDE_DOMAIN'),None
            values[b.name]=a
        for condition in scope.nonzero:
            if interval(condition,values).contains_zero():return Proof('UNKNOWN','NUMERICAL_CONDITION_UNPROVEN'),None
        d=dimension(case.expression,scope.symbol_units);out=unit(case.output_unit)
        if d is not None and d!=out.dimensions:return Proof('DISPROVED','NUMERICAL_RESULT_DIMENSION_MISMATCH'),None
        reference_interval=interval(reference.expression,values)  # Retain the original reference domain, even after cancellation.
        expected=from_si(interval(case.expression,values),case.output_unit)
        reported=Interval(rational(case.reported_lo),rational(case.reported_hi))
        if reference.mode=='interval':
            if reported.hi-reported.lo>rational(reference.max_interval_width):return Proof('DISPROVED','NUMERICAL_ENCLOSURE_TOO_WIDE'),expected
            if reported.lo<=expected.lo and reported.hi>=expected.hi:return Proof('PROVED','CONSERVATIVE_INTERVAL_ENCLOSURE'),expected
            if reported.hi<expected.lo or reported.lo>expected.hi:return Proof('DISPROVED','NUMERICAL_INTERVAL_DISJOINT'),expected
            return Proof('UNKNOWN','NUMERICAL_ENCLOSURE_OR_DEPENDENCY_REVIEW'),expected
        if reported.lo!=reported.hi:return Proof('DISPROVED','POINT_REPORT_IS_INTERVAL'),expected
        if expected.lo!=expected.hi:return Proof('UNKNOWN','POINT_PRECISION_NOT_PROVEN'),expected
        if reference.mode=='rounded_point':
            target=rounded_text(expected.lo,reference.decimal_places)
            if case.reported_lo!=target or case.reported_hi!=target:return Proof('DISPROVED','ROUNDING_OR_PRECISION_MISMATCH'),expected
            return Proof('PROVED','EXACT_HALF_EVEN_ROUNDING'),expected
        allowance=max(rational(reference.abs_tolerance),rational(reference.rel_tolerance)*abs(expected.lo))
        err=abs(reported.lo-expected.lo)
        return Proof('PROVED' if err<=allowance else 'DISPROVED','NUMERICAL_WITHIN_OPERATOR_TOLERANCE' if err<=allowance else 'NUMERICAL_OUTSIDE_TOLERANCE'),expected
    except ContractError as exc:
        hard={'UNIT_DIMENSION_OR_KIND_MISMATCH','BELOW_ABSOLUTE_ZERO','DIVISION_INTERVAL_CONTAINS_ZERO','SQRT_DOMAIN_INVALID','ZERO_TO_NONPOSITIVE_POWER','ADDITION_DIMENSION_MISMATCH','DIMENSIONAL_FUNCTION_ARGUMENT'}
        return Proof('DISPROVED' if exc.code in hard else 'UNKNOWN',exc.code),None
