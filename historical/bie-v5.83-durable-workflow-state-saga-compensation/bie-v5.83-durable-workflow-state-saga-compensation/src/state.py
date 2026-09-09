STATES=("PENDING","RUNNING","WAITING","SUCCEEDED",
        "FAILED","COMPENSATING","COMPENSATED","TIMED_OUT","CANCELLED","COMPLETED")

ALLOWED={
 "PENDING":{"RUNNING","CANCELLED"},
 "RUNNING":{"SUCCEEDED","FAILED","WAITING","TIMED_OUT","CANCELLED"},
 "WAITING":{"RUNNING","TIMED_OUT","CANCELLED"},
 "FAILED":{"COMPENSATING","CANCELLED"},
 "TIMED_OUT":{"COMPENSATING","CANCELLED"},
 "COMPENSATING":{"COMPENSATED","FAILED"},
 "SUCCEEDED":{"COMPLETED"},
 "COMPENSATED":{"COMPLETED"},
 "CANCELLED":{"COMPLETED"},
 "COMPLETED":set()
}

def transition(state,target):
    if target not in ALLOWED.get(state,set()):
        raise ValueError("INVALID_WORKFLOW_TRANSITION")
    return target

def workflow(workflow_id,version="1"):
    return {"workflow_id":workflow_id,"version":version,
            "state":"PENDING","steps":{},"history":[]}
