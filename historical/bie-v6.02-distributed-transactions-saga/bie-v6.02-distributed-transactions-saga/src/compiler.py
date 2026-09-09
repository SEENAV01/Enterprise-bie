from saga import saga,step
from state import saga_state
from consistency import consistency_policy

def compile_saga(saga_id,workflow_id,
                 step_defs,mode="COMPENSATABLE"):
    steps=[step(**x) for x in step_defs]
    s=saga(saga_id,workflow_id,steps,mode)
    state=saga_state(saga_id,"STARTED")
    policy=consistency_policy(mode)
    return {"schema_version":"6.02",
            "saga":s,"state":state,
            "consistency_policy":policy,
            "quality_gate":{"valid":True,"errors":[]}}
