def ownership(artifact_id,owner_id,scope="WORKSPACE"):
    return {"artifact_id":artifact_id,"owner_id":owner_id,
            "scope":scope}

def transfer(record,new_owner):
    out=dict(record); out["owner_id"]=new_owner
    return out
