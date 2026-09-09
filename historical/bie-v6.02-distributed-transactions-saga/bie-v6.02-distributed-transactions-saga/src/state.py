def saga_state(saga_id,status,
              completed_steps=None,
              failed_step=None):
    return {"saga_id":saga_id,"status":status,
            "completed_steps":completed_steps or [],
            "failed_step":failed_step}

def transition(state,status,**kwargs):
    out=dict(state); out["status"]=status
    out.update(kwargs)
    return out
