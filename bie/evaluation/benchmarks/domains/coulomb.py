"""PHY-001: electrostatic point charges in vacuum; signed vector superposition."""
from __future__ import annotations
import math
from ..models import BenchmarkError, exact_fields, number
from .common import integer, scalar, vector

REFERENCE_K = 8.9875517923e9  # pinned numerical model, not a claim of an exact SI constant


def solve(data: dict) -> dict:
    exact_fields(data, {"op", "charges", "target_index"}, {"k_N_m2_per_C2"})
    if data["op"] != "force_on_charge":
        raise BenchmarkError("UNSUPPORTED_OPERATION")
    charges = data["charges"]
    if type(charges) is not list or not 2 <= len(charges) <= 128:
        raise BenchmarkError("INVALID_CHARGE_COUNT")
    parsed = []
    for charge in charges:
        exact_fields(charge, {"q", "position"})
        parsed.append((scalar(charge["q"], "charge"), vector(charge["position"], "length")))
    index = integer(data["target_index"], 0, len(parsed) - 1)
    k = number(data.get("k_N_m2_per_C2", REFERENCE_K), maximum=1e15)
    if k <= 0:
        raise BenchmarkError("NONPOSITIVE_COULOMB_CONSTANT")
    qt, rt = parsed[index]
    components: list[list[float]] = [[], [], []]
    for j, (q, r) in enumerate(parsed):
        if j == index:
            continue
        d = [rt[i] - r[i] for i in range(3)]
        distance = math.hypot(*d)
        if distance < 1e-15:
            raise BenchmarkError("COINCIDENT_OR_UNRESOLVED_POINT_CHARGES")
        magnitude_signed = number(k * qt * q / (distance * distance))
        for i in range(3):
            components[i].append(number(magnitude_signed * d[i] / distance))
    force = [number(math.fsum(c)) for c in components]
    return {"force_N": force, "magnitude_N": number(math.hypot(*force))}
