from __future__ import annotations
from dataclasses import dataclass, replace
from typing import Iterable
from bie.pedagogy.pedagogy_provenance import _normalize_ids
from bie.pedagogy.objective_taxonomy import LEVELS

@dataclass(frozen=True)
class AssessmentCell:
    objective_id: str
    concept_id: str
    cognitive_level: str
    misconception_id: str | None
    transfer: bool
    item_ids: tuple[str,...]
    evidence_ids: tuple[str,...]

@dataclass(frozen=True)
class AssessmentBlueprintReport:
    cells: tuple[AssessmentCell,...]
    uncovered_requirements: tuple[tuple[str,str,str,bool],...]
    passed: bool

def build_assessment_blueprint(
    requirements: Iterable[tuple[str,str,str,bool]],
    cells: Iterable[AssessmentCell],
) -> AssessmentBlueprintReport:
    req=tuple(sorted(set(requirements)))
    cs=tuple(sorted((replace(c, item_ids=_normalize_ids(c.item_ids,"assessment items"),
                            evidence_ids=_normalize_ids(c.evidence_ids,"assessment evidence")) for c in cells),
                    key=lambda x:(x.objective_id,x.concept_id,x.cognitive_level,x.transfer,x.misconception_id or "")))
    if not req:
        raise ValueError("requirements")
    for oid,cid,level,transfer in req:
        if not oid.strip() or not cid.strip() or level not in LEVELS or type(transfer) is not bool:
            raise ValueError("invalid requirement")
    coverage=set()
    for c in cs:
        if not c.objective_id.strip() or not c.concept_id.strip() or c.cognitive_level not in LEVELS or type(c.transfer) is not bool:
            raise ValueError("invalid cell")
        if not c.item_ids or not c.evidence_ids:
            raise ValueError("cell requires items and provenance")
        coverage.add((c.objective_id,c.concept_id,c.cognitive_level,c.transfer))
    missing=tuple(x for x in req if x not in coverage)
    return AssessmentBlueprintReport(cs,missing,not missing)
