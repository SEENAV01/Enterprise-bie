def saga(saga_id,steps):
    return {"saga_id":saga_id,
            "steps":steps,
            "status":"RUNNING"}

def compensate(record,completed_steps):
    return {"saga_id":record["saga_id"],
            "compensated_steps":list(reversed(completed_steps)),
            "status":"COMPENSATING"}
