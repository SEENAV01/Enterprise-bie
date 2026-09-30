"""Bounded typed primitives for Batch002's authored structured references.

These helpers validate data; they never execute candidate expressions or fetch URLs.
Rational values are exact within a deliberately bounded educational profile.
"""
from __future__ import annotations
from fractions import Fraction
from ..models import BenchmarkError, canonical_json, exact_fields, ident
from .common import rational


def record(value: object, fields: set[str]) -> dict:
    canonical_json(value)
    return exact_fields(value, fields)


def choice(value: object, options) -> str:
    if type(value) is not str or value not in options:
        raise BenchmarkError('UNSUPPORTED_ENUM')
    return value


def sequence(value: object, *, lower: int = 1, upper: int = 64) -> list:
    if type(value) is not list or not lower <= len(value) <= upper:
        raise BenchmarkError('COLLECTION_SIZE_OR_TYPE')
    return value


def unique_ids(value: object, *, lower: int = 1, upper: int = 64) -> list[str]:
    items = [ident(v) for v in sequence(value, lower=lower, upper=upper)]
    if len(set(items)) != len(items):
        raise BenchmarkError('DUPLICATE_ID')
    return items


def amount(value: object, *, positive: bool = False, signed: bool = False,
           maximum: int = 10**12) -> Fraction:
    # Fractions arise only inside validated unit conversion. Public records
    # remain JSON-only; preserve the same rational resource bound internally.
    q = value if type(value) is Fraction else rational(value)
    if q.numerator.bit_length() > 512 or q.denominator.bit_length() > 512:
        raise BenchmarkError("RATIONAL_SIZE_LIMIT")
    if abs(q) > maximum or (positive and q <= 0) or (not signed and q < 0):
        raise BenchmarkError('QUANTITY_OUT_OF_PROFILE')
    return q


def probability(value: object) -> Fraction:
    q = amount(value)
    if q > 1:
        raise BenchmarkError('INVALID_PROBABILITY')
    return q


def exact_map(values: dict[str, Fraction | int]) -> dict[str, str]:
    return {key: str(value) for key, value in sorted(values.items())}


def quantity(value: object, units: dict[str, Fraction | int], *, positive=False,
             signed=False) -> Fraction:
    record(value, {'value', 'unit'})
    unit = choice(value['unit'], units)
    return amount(amount(value['value'], signed=signed) * units[unit],
                  positive=positive, signed=signed)


def observed_claims(actual: object, reference: dict[str, str | bool]) -> dict:
    """Exact proposition-profile audit, NOT natural-language entailment.

    References stay in trusted evaluator code. Unknown and missing propositions
    remain explicit defects, so a candidate cannot win by omitting a claim.
    """
    if type(actual) is not dict or len(actual) > 64:
        raise BenchmarkError('INVALID_CLAIM_MAP')
    defects = []
    for key in sorted(set(actual) | set(reference)):
        ident(key)
        if key not in reference:
            defects.append({'claim': key, 'reason': 'UNKNOWN_CLAIM'})
        elif key not in actual:
            defects.append({'claim': key, 'reason': 'MISSING_CLAIM'})
        elif type(actual[key]) is not type(reference[key]) or actual[key] != reference[key]:
            defects.append({'claim': key, 'reason': 'CONTRADICTED_CLAIM'})
    return {'consistent': not defects, 'defects': defects,
            'assessment_scope': 'DECLARED_PROPOSITION_PROFILE_ONLY'}
