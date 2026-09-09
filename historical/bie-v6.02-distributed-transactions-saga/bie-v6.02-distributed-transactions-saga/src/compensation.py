def compensation(step_id,action,
                   idempotency_key=None):
    return {"step_id":step_id,"action":action,
            "idempotency_key":idempotency_key,
            "status":"PENDING"}

def compensation_order(completed_steps):
    return list(reversed(completed_steps))
