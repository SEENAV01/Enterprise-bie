"""MATH-002: bounded analytic references; no eval(), sample-fit proof or CAS claim."""
from __future__ import annotations
from fractions import Fraction
import math
from ..models import BenchmarkError, exact_fields, number
from .common import derivative, fraction_result, horner, integer, polynomial, rational, trim


def solve(data: dict) -> dict:
    if type(data) is not dict:
        raise BenchmarkError("INVALID_FIELDS")
    op = data.get("op")
    if op == "differentiate_polynomial":
        exact_fields(data, {"op", "coefficients", "order"})
        p = polynomial(data["coefficients"])
        for _ in range(integer(data["order"], 0, 8)):
            p = derivative(p)
        return {"coefficients": [str(c) for c in trim(p)]}
    if op == "antiderivative_polynomial":
        exact_fields(data, {"op", "coefficients"})
        p = polynomial(data["coefficients"])
        anti = (Fraction(0),) + tuple(c/Fraction(i+1) for i, c in enumerate(p))
        return {"particular_coefficients": [str(c) for c in trim(anti)], "arbitrary_constant": "C"}
    if op == "definite_integral_polynomial":
        exact_fields(data, {"op", "coefficients", "lower", "upper"})
        p = polynomial(data["coefficients"])
        anti = (Fraction(0),) + tuple(c/Fraction(i+1) for i, c in enumerate(p))
        return fraction_result(horner(anti, rational(data["upper"])) - horner(anti, rational(data["lower"])))
    if op == "tangent_polynomial":
        exact_fields(data, {"op", "coefficients", "x"})
        p, x = polynomial(data["coefficients"]), rational(data["x"])
        slope = horner(derivative(p), x)
        intercept = horner(p, x) - slope*x
        return {"slope_exact": str(slope), "intercept_exact": str(intercept)}
    if op == "derivative_absolute_value":
        exact_fields(data, {"op", "x"})
        x = rational(data["x"])
        if x == 0:
            raise BenchmarkError("NONDIFFERENTIABLE_AT_POINT")
        return {"derivative": 1 if x > 0 else -1}
    if op == "definite_integral_reciprocal":
        exact_fields(data, {"op", "lower", "upper"})
        a, b = rational(data["lower"]), rational(data["upper"])
        if a == 0 or b == 0 or (a < 0) != (b < 0):
            raise BenchmarkError("INTEGRATION_INTERVAL_CROSSES_SINGULARITY")
        return {"value": number(math.log(abs(float(b))) - math.log(abs(float(a))))}
    raise BenchmarkError("UNSUPPORTED_OPERATION")
