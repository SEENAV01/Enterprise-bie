
from dataclasses import dataclass
ALLOWED={
"PLANNED":{"READY","BLOCKED","INVALIDATED"},
"READY":{"IN_PROGRESS","BLOCKED","INVALIDATED"},
"IN_PROGRESS":{"IMPLEMENTED","BLOCKED","INVALIDATED"},
"IMPLEMENTED":{"UNIT_TESTED","IN_PROGRESS","INVALIDATED"},
"UNIT_TESTED":{"INTEGRATION_TESTED","IN_PROGRESS","INVALIDATED"},
"INTEGRATION_TESTED":{"GOLDEN_TESTED","QA_VERIFIED","IN_PROGRESS","INVALIDATED"},
"GOLDEN_TESTED":{"QA_VERIFIED","IN_PROGRESS","INVALIDATED"},
"QA_VERIFIED":{"ACCEPTED","IN_PROGRESS","INVALIDATED"},
"ACCEPTED":{"INVALIDATED"},
"BLOCKED":{"PLANNED","READY","INVALIDATED"},
"INVALIDATED":{"PLANNED"},
}
class LifecycleError(ValueError): pass
@dataclass(frozen=True)
class Transition:
    task_id:str; from_status:str; to_status:str; reason:str; evidence_refs:tuple=()
def transition(task_id,current,target,reason,evidence_refs=()):
    if target not in ALLOWED.get(current,set()): raise LifecycleError(f"illegal transition {current}->{target}")
    if not reason.strip(): raise LifecycleError("reason required")
    if target in {"UNIT_TESTED","INTEGRATION_TESTED","GOLDEN_TESTED","QA_VERIFIED","ACCEPTED"} and not evidence_refs:
        raise LifecycleError("verification transition requires evidence")
    return Transition(task_id,current,target,reason,tuple(evidence_refs))
