"""RE-TEMP-033 — Plan temporal queries by required reasoning capability."""
from dataclasses import dataclass
@dataclass(frozen=True)
class TemporalQuery:
    relation:str
    needs_uncertainty:bool=False
    needs_provenance:bool=False
def plan_temporal_query(q:TemporalQuery):
    relation=q.relation.lower().strip()
    mapping={"before":"ORDER","after":"ORDER","during":"INTERVAL","overlaps":"INTERVAL","duration":"DURATION","recurs":"RECURRENCE"}
    if relation not in mapping: return ("ABSTAIN_UNSUPPORTED_RELATION",)
    plan=[mapping[relation]]
    if q.needs_uncertainty: plan.append("UNCERTAINTY")
    if q.needs_provenance: plan.append("PROVENANCE")
    return tuple(plan)
