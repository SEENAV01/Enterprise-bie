"""Explicit units, bounded arithmetic and exact polynomial helpers."""
from __future__ import annotations
from fractions import Fraction
import re
from ..models import BenchmarkError, exact_fields, number

UNITS = {
    "C": ("charge", 1), "uC": ("charge", 1e-6), "nC": ("charge", 1e-9),
    "m": ("length", 1), "cm": ("length", .01), "mm": ("length", .001), "km": ("length", 1000),
    "kg": ("mass", 1), "g": ("mass", .001),
    "s": ("time", 1), "ms": ("time", .001),
    "N": ("force", 1), "kN": ("force", 1000),
    "m/s": ("speed", 1), "km/h": ("speed", 1 / 3.6),
    "m/s^2": ("acceleration", 1),
    "Hz": ("frequency", 1), "kHz": ("frequency", 1000),
    "rad": ("angle", 1), "deg": ("angle", 3.141592653589793 / 180),
    "m^2": ("area", 1), "cm^2": ("area", .0001),
}


def scalar(q: dict, dimension: str, *, positive: bool = False, nonnegative: bool = False) -> float:
    exact_fields(q, {"value", "unit"})
    unit = q["unit"]
    if type(unit) is not str or unit not in UNITS or UNITS[unit][0] != dimension:
        raise BenchmarkError("UNIT_DIMENSION_MISMATCH")
    value = number(number(q["value"], maximum=1e30) * UNITS[unit][1], maximum=1e30)
    if positive and value <= 0 or nonnegative and value < 0:
        raise BenchmarkError("NONPOSITIVE_QUANTITY" if positive else "NEGATIVE_QUANTITY")
    return value


def vector(q: dict, dimension: str, size: int = 3) -> tuple[float, ...]:
    exact_fields(q, {"values", "unit"})
    if type(q["values"]) is not list or len(q["values"]) != size:
        raise BenchmarkError("VECTOR_DIMENSION_MISMATCH")
    return tuple(scalar({"value": v, "unit": q["unit"]}, dimension) for v in q["values"])


def integer(value: object, lower: int, upper: int) -> int:
    if type(value) is not int or not lower <= value <= upper:
        raise BenchmarkError("INVALID_INTEGER")
    return value


def rational(value: object) -> Fraction:
    if type(value) is str:
        if len(value) > 120 or re.fullmatch(r"[+-]?\d+(?:/[1-9]\d*)?", value) is None:
            raise BenchmarkError("INVALID_RATIONAL")
        q = Fraction(value)
    elif type(value) in (int, float):
        number(value, maximum=1e30)
        q = Fraction(str(value))
    else:
        raise BenchmarkError("INVALID_RATIONAL")
    if q.numerator.bit_length() > 512 or q.denominator.bit_length() > 512:
        raise BenchmarkError("RATIONAL_SIZE_LIMIT")
    return q


def polynomial(values: object) -> tuple[Fraction, ...]:
    if type(values) is not list or not 1 <= len(values) <= 33:
        raise BenchmarkError("POLYNOMIAL_DEGREE_LIMIT")
    return tuple(rational(c) for c in values)


def horner(coefficients: tuple[Fraction, ...], x: Fraction) -> Fraction:
    result = Fraction(0)
    for c in reversed(coefficients):
        result = result * x + c
        if result.numerator.bit_length() > 16384 or result.denominator.bit_length() > 16384:
            raise BenchmarkError("ARITHMETIC_SIZE_LIMIT")
    return result


def trim(coefficients: tuple[Fraction, ...]) -> tuple[Fraction, ...]:
    items = list(coefficients) or [Fraction(0)]
    while len(items) > 1 and items[-1] == 0:
        items.pop()
    return tuple(items)


def derivative(coefficients: tuple[Fraction, ...]) -> tuple[Fraction, ...]:
    return trim(tuple(i * c for i, c in enumerate(coefficients) if i))


def fraction_result(value: Fraction) -> dict:
    try:
        approximation = float(value)
    except (OverflowError, ValueError) as exc:
        raise BenchmarkError("NUMERIC_REPRESENTATION_LIMIT") from exc
    if value != 0 and approximation == 0:
        raise BenchmarkError("NUMERIC_REPRESENTATION_LIMIT")
    return {"exact": str(value), "value": number(approximation)}
