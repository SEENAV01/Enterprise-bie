"""RE-TEMP-038 — Preserve parent-result lineage for derived temporal conclusions."""
from dataclasses import dataclass
@dataclass(frozen=True)
class DerivedTemporalResult:
    result_id:str
    conclusion:str
    parent_result_ids:tuple[str,...]
    evidence_ids:tuple[str,...]
def build_derived_temporal_result(result_id,conclusion,parent_results,evidence_ids=()):
    parents=tuple(sorted(set(parent_results))); evidence=tuple(sorted(set(evidence_ids)))
    if not result_id or not conclusion: raise ValueError("result_id and conclusion required")
    if not parents: raise ValueError("derived result requires parent lineage")
    if result_id in parents: raise ValueError("result cannot be its own parent")
    return DerivedTemporalResult(result_id,conclusion,parents,evidence)
