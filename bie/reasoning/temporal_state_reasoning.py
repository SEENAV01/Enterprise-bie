from __future__ import annotations
from dataclasses import dataclass,asdict
from bie.reasoning.grounded_result import identifier,require_refs,inference,evidence
TASK_ID="BIE-RE-TEMP-015"
@dataclass(frozen=True)
class StateChange:
    entity_id:str; tick:int; state:str; evidence_ids:tuple[str,...]
def state_at(changes,tick,refs):
    refs=evidence(refs); changes=tuple(changes)
    if not changes: raise ValueError("At least one state change required")
    entities={c.entity_id for c in changes}
    if len(entities)!=1: raise ValueError("State history must describe one entity")
    for c in changes: identifier(c.entity_id); identifier(c.state,"state"); require_refs(c.evidence_ids,refs)
    ordered=sorted(changes,key=lambda c:(c.tick,c.state))
    if len({c.tick for c in ordered})!=len(ordered):
        return inference(TASK_ID,"temporal.state_at",{"changes":[asdict(c) for c in ordered],"tick":tick},{"state":None,"witness_tick":None},refs,status="CONFLICT",uncertainty=("Multiple state changes share a tick",))
    prior=[c for c in ordered if c.tick<=tick]
    if not prior: return inference(TASK_ID,"temporal.state_at",{"changes":[asdict(c) for c in ordered],"tick":tick},{"state":None,"witness_tick":None},refs,status="UNREACHABLE",uncertainty=("No evidenced state exists at or before query time",))
    c=prior[-1]
    return inference(TASK_ID,"temporal.state_at",{"changes":[asdict(x) for x in ordered],"tick":tick},{"state":c.state,"witness_tick":c.tick,"entity_id":c.entity_id},refs,assumptions=("State persists until the next evidenced transition",))
