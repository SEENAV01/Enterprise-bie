def control(control_id,name,
           requirement,owner=None):
    return {"control_id":control_id,
            "name":name,
            "requirement":requirement,
            "owner":owner}

def mapping(control_id,evidence_refs,
            status="PENDING"):
    return {"control_id":control_id,
            "evidence_refs":evidence_refs,
            "status":status}
