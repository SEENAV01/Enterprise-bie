"""RE-TEMP-005: explicit elapsed-time and duration reasoning on compatible axes."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from bie.reasoning.chronology_reasoning import TimeSpan
from bie.reasoning.grounded_result import evidence, identifier, inference, require_refs
TASK_ID="BIE-RE-TEMP-005"

@dataclass(frozen=True)
class DurationClaim:
    claim_id:str
    start:TimeSpan
    end:TimeSpan
    evidence_ids:tuple[str,...]


def duration(claim:DurationClaim, refs):
    refs=evidence(refs); identifier(claim.claim_id,"claim id"); require_refs(claim.evidence_ids,refs)
    if not isinstance(claim.start,TimeSpan) or not isinstance(claim.end,TimeSpan): raise ValueError("Duration endpoints require TimeSpan")
    if claim.start.axis!=claim.end.axis: raise ValueError("Incompatible time axes")
    s,e=claim.start,claim.end
    if s.earliest is None or s.latest is None or e.earliest is None or e.latest is None:
        return inference(TASK_ID,"temporal.duration",asdict(claim),{"axis":s.axis,"unit":"year" if s.axis=="historical_year" else "day","minimum":None,"maximum":None},refs,status="AMBIGUOUS",uncertainty=("Open endpoint bounds prevent finite duration bounds",))
    minimum=e.earliest-s.latest
    maximum=e.latest-s.earliest
    if maximum < 0:
        return inference(TASK_ID,"temporal.duration",asdict(claim),{"axis":s.axis,"unit":"year" if s.axis=="historical_year" else "day","minimum":minimum,"maximum":maximum},refs,status="CONFLICT",uncertainty=("End is proven earlier than start",))
    if minimum < 0:
        return inference(TASK_ID,"temporal.duration",asdict(claim),{"axis":s.axis,"unit":"year" if s.axis=="historical_year" else "day","minimum":0,"maximum":maximum},refs,status="AMBIGUOUS",assumptions=("Negative elapsed time is not emitted as a valid duration",),uncertainty=("Uncertain endpoints permit both zero/positive and reversed order",))
    return inference(TASK_ID,"temporal.duration",asdict(claim),{"axis":s.axis,"unit":"year" if s.axis=="historical_year" else "day","minimum":minimum,"maximum":maximum,"exact":minimum==maximum},refs)
