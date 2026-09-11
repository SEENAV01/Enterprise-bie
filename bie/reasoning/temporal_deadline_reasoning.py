from __future__ import annotations
from dataclasses import asdict
from bie.reasoning.chronology_reasoning import TimeSpan
from bie.reasoning.grounded_result import inference
TASK_ID="BIE-RE-TEMP-016"
def deadline_status(actual:TimeSpan, deadline:TimeSpan, refs):
    if actual.axis!=deadline.axis: raise ValueError("Incompatible time axes")
    if deadline.earliest!=deadline.latest or deadline.earliest is None: raise ValueError("Deadline must be an evidenced point")
    d=deadline.earliest
    if actual.latest is not None and actual.latest<=d: status="RESOLVED"; label="ON_TIME"
    elif actual.earliest is not None and actual.earliest>d: status="RESOLVED"; label="LATE"
    else: status="AMBIGUOUS"; label="INDETERMINATE"
    return inference(TASK_ID,"temporal.deadline_status",{"actual":asdict(actual),"deadline":asdict(deadline)},{"classification":label,"deadline_tick":d},refs,status=status,uncertainty=("Actual-time uncertainty crosses the deadline",) if status=="AMBIGUOUS" else ())
