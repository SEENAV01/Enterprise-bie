"""MATH-001: exact bounded polynomial/rational and finite-relation checks."""
from __future__ import annotations
from ..models import BenchmarkError, exact_fields
from .common import fraction_result, horner, polynomial, rational


def solve(data: dict) -> dict:
    if type(data) is not dict:
        raise BenchmarkError("INVALID_FIELDS")
    op = data.get("op")
    if op == "polynomial_value":
        exact_fields(data, {"op", "coefficients", "x"})
        return fraction_result(horner(polynomial(data["coefficients"]), rational(data["x"])))
    if op == "rational_value":
        exact_fields(data, {"op", "numerator", "denominator", "x"})
        x = rational(data["x"])
        n, d = polynomial(data["numerator"]), polynomial(data["denominator"])
        denominator = horner(d, x)
        if denominator == 0:
            raise BenchmarkError("OUTSIDE_ORIGINAL_DOMAIN")
        # Never cancel away an original denominator restriction.
        return fraction_result(horner(n, x) / denominator)
    if op == "composition_value":
        exact_fields(data, {"op", "outer", "inner", "x"})
        inner = horner(polynomial(data["inner"]), rational(data["x"]))
        return fraction_result(horner(polynomial(data["outer"]), inner))
    if op == "inverse_affine_value":
        exact_fields(data, {"op", "a", "b", "y"})
        a, b, y = rational(data["a"]), rational(data["b"]), rational(data["y"])
        if a == 0:
            raise BenchmarkError("NONINVERTIBLE_FUNCTION")
        return fraction_result((y-b)/a)
    if op == "finite_relation":
        exact_fields(data, {"op", "pairs"})
        if type(data["pairs"]) is not list or not 1 <= len(data["pairs"]) <= 256:
            raise BenchmarkError("INVALID_RELATION")
        mapping: dict = {}
        all_y: set = set()
        conflicts: set = set()
        for pair in data["pairs"]:
            if type(pair) is not list or len(pair) != 2:
                raise BenchmarkError("INVALID_RELATION_PAIR")
            x, y = rational(pair[0]), rational(pair[1])
            if x in mapping and mapping[x] != y:
                conflicts.add(x)
            mapping[x] = y
            all_y.add(y)
        is_function = not conflicts
        return {"is_function": is_function, "is_injective": is_function and len(all_y) == len(mapping),
                "domain_cardinality": len(mapping), "conflicting_inputs": [str(x) for x in sorted(conflicts)]}
    raise BenchmarkError("UNSUPPORTED_OPERATION")
