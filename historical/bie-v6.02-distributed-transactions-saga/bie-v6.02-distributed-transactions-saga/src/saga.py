def saga(saga_id,workflow_id,steps,
         consistency="COMPENSATABLE"):
    return {"saga_id":saga_id,"workflow_id":workflow_id,
            "steps":steps,"consistency":consistency,
            "status":"STARTED"}

def step(step_id,action,compensation=None,
         idempotency_key=None):
    return {"step_id":step_id,"action":action,
            "compensation":compensation,
            "idempotency_key":idempotency_key,
            "status":"PENDING"}
