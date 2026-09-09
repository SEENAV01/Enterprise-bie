def hold(hold_id,artifact_id,hold_type,reason,active=True):
    return {"hold_id":hold_id,"artifact_id":artifact_id,
            "hold_type":hold_type,"reason":reason,"active":active}

def deletion_blocked(artifact_id,holds):
    return any(h.get("artifact_id")==artifact_id and
               h.get("active") for h in holds)
