"""Structured diagnostic execution and exact-denominator grading.

The bundled reference calculator is for local diagnostics. A live BIE adapter
must supply its own outputs. Neither path measures teaching, cinema, learning,
source grounding, rendered media or gameplay: later EVAL metrics own those.
"""
from __future__ import annotations
from importlib import import_module
import math
from pathlib import Path
from typing import Any
from .models import BenchmarkCase, BenchmarkError, canonical_json, digest, number, strict_loads

PACK_MODULES = {
    "BIE-EVAL-PHY-001": "coulomb", "BIE-EVAL-PHY-002": "mechanics", "BIE-EVAL-PHY-003": "waves",
    "BIE-EVAL-MATH-001": "functions", "BIE-EVAL-MATH-002": "calculus", "BIE-EVAL-MATH-003": "geometry",
    "BIE-EVAL-BIO-001": "photosynthesis",
    "BIE-EVAL-BIO-002": "genetics",
    "BIE-EVAL-BIO-003": "physiology",
    "BIE-EVAL-CHEM-001": "bonding",
    "BIE-EVAL-CHEM-002": "mechanisms",
    "BIE-EVAL-CHEM-003": "stoichiometry",
    "BIE-EVAL-HIST-001": "french_revolution",
    "BIE-EVAL-HIST-002": "historical_causality",
    "BIE-EVAL-HIST-003": "chronology",
    "BIE-EVAL-GEO-001": "plate_tectonics",
    "BIE-EVAL-GEO-002": "maps",
    "BIE-EVAL-GEO-003": "climate",
    "BIE-EVAL-CIV-001": "civics",
    "BIE-EVAL-DATA-001": "tables_charts",

}


def load_pack(task_id: str) -> tuple[BenchmarkCase, ...]:
    if type(task_id) is not str or task_id not in PACK_MODULES:
        raise BenchmarkError("UNKNOWN_PACK")
    file = Path(__file__).with_name("data") / (task_id + ".json")
    if not file.is_file():
        raise BenchmarkError("PACK_NOT_INSTALLED")
    body = strict_loads(file.read_bytes())
    if type(body) is not list or not body:
        raise BenchmarkError("INVALID_PACK")
    cases = tuple(BenchmarkCase.from_dict(c) for c in body)
    if any(c.task_id != task_id for c in cases) or len({c.case_id for c in cases}) != len(cases):
        raise BenchmarkError("PACK_IDENTITY_MISMATCH")
    return cases


def reference_output(task_id: str, inputs: dict) -> dict:
    if type(task_id) is not str or task_id not in PACK_MODULES:
        raise BenchmarkError("UNKNOWN_PACK")
    canonical_json(inputs)
    module = import_module(".domains." + PACK_MODULES[task_id], package=__package__)
    try:
        value = module.solve(inputs)
        canonical_json(value)
        return {"status": "OK", "values": value}
    except BenchmarkError as exc:
        return {"status": "REJECTED", "error_code": exc.code}
    # Unexpected programmer/runtime failures are NOT academic rejections.


def compare_structured(expected: Any, actual: Any, *, atol: float, rtol: float,
                       path: str = "$") -> tuple[dict, ...]:
    differences: list[dict] = []
    if type(expected) in (int, float):
        if type(actual) not in (int, float):
            differences.append({"path": path, "reason": "NUMERIC_TYPE_MISMATCH"})
        else:
            try:
                n = number(actual)
            except BenchmarkError:
                differences.append({"path": path, "reason": "NONFINITE_OUTPUT"})
            else:
                if not math.isclose(float(expected), n, abs_tol=atol, rel_tol=rtol):
                    differences.append({"path": path, "reason": "NUMERIC_MISMATCH"})
    elif type(expected) is dict:
        if type(actual) is not dict or set(expected) != set(actual):
            differences.append({"path": path, "reason": "OBJECT_SCHEMA_MISMATCH"})
        else:
            for key in sorted(expected):
                differences.extend(compare_structured(expected[key], actual[key], atol=atol, rtol=rtol, path=path+"."+key))
    elif type(expected) is list:
        if type(actual) is not list or len(actual) != len(expected):
            differences.append({"path": path, "reason": "ARRAY_SCHEMA_MISMATCH"})
        else:
            for i, (e,a) in enumerate(zip(expected, actual)):
                differences.extend(compare_structured(e, a, atol=atol, rtol=rtol, path=f"{path}[{i}]"))
    elif type(actual) is not type(expected) or actual != expected:
        differences.append({"path": path, "reason": "VALUE_OR_TYPE_MISMATCH"})
    return tuple(differences)


def grade_case(case: BenchmarkCase, output: dict, *, evaluator_id: str = "structured-reference-v1") -> dict:
    from .models import ident
    ident(evaluator_id)
    canonical_json(output)  # rejects NaN, unknown objects, deep/oversized answer injection
    differences = compare_structured(case.expected, output,
        atol=case.absolute_tolerance, rtol=case.relative_tolerance)
    return {"case_id": case.case_id, "case_sha256": case.content_sha256,
        "output_sha256": digest(output), "evaluator_id": evaluator_id,
        "status": "FAIL" if differences else "PASS", "differences": list(differences),
        "evidence_grade": case.evidence_grade, "release_authorized": False,
        "product_accepted": False}


def diagnostic_pack(task_id: str) -> dict:
    results = [grade_case(c, reference_output(task_id, c.inputs)) for c in load_pack(task_id)]
    return {"task_id": task_id, "execution_kind": "AUTHORED_DIAGNOSTIC_REFERENCE_REPLAY",
            "results": results, "case_count": len(results),
            "passed": sum(r["status"] == "PASS" for r in results),
            "live_bie_run": False, "golden_certified": False, "product_accepted": False}
