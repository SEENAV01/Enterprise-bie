from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping, Iterable

@dataclass(frozen=True)
class PedagogyReadinessReport:
    passed: bool
    failed_checks: tuple[str,...]
    review_items: tuple[str,...]
    provenance_complete: bool
    reproducible: bool

def pedagogy_readiness_gate(
    checks: Mapping[str,bool],
    *,
    review_items: Iterable[str]=(),
    provenance_complete: bool,
    reproducible: bool,
) -> PedagogyReadinessReport:
    required={
        "objective_coverage","prerequisite_coverage","assessment_alignment",
        "cognitive_load_safe","realbook_fixture","integration_contract"
    }
    missing=required-set(checks)
    if missing:
        raise ValueError("missing readiness checks: "+",".join(sorted(missing)))
    if any(type(v) is not bool for v in checks.values()) or type(provenance_complete) is not bool or type(reproducible) is not bool:
        raise ValueError("readiness checks must be explicit booleans")
    failed=tuple(sorted(k for k,v in checks.items() if not bool(v)))
    reviews=tuple(sorted(set(x for x in review_items if str(x).strip())))
    passed=not failed and not reviews and provenance_complete and reproducible
    return PedagogyReadinessReport(passed,failed,reviews,provenance_complete,reproducible)
