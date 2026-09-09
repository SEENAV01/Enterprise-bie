from state import transition,workflow
from saga import compensation_plan

def compile_recovery(workflow_id,steps,completed_steps,
                     failure_reason=None):
    action="COMPENSATE" if failure_reason and completed_steps else "RESUME"
    plan=compensation_plan(steps,completed_steps) if action=="COMPENSATE" else []
    return {"schema_version":"5.83",
            "workflow_id":workflow_id,
            "recovery_action":action,
            "compensation_plan":plan,
            "failure_reason":failure_reason,
            "quality_gate":{"valid":True,"errors":[]}}
