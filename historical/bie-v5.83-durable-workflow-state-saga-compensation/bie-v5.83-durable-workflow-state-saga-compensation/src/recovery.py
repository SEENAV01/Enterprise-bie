def recovery_action(state,has_checkpoint=True):
    if state in {"RUNNING","WAITING"} and has_checkpoint:
        return "RESUME_FROM_CHECKPOINT"
    if state in {"FAILED","TIMED_OUT"}:
        return "COMPENSATE"
    if state=="CANCELLED":
        return "CLOSE"
    return "CONTINUE"

def recover(workflow_record,checkpoint_record=None):
    if checkpoint_record:
        workflow_record["state"]=checkpoint_record["state"]
        workflow_record["recovered_from_sequence"]=checkpoint_record["sequence"]
        workflow_record["completed_steps"]=checkpoint_record["completed_steps"]
    return workflow_record
