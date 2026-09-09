def policy(policy_id,name,scope,parameters=None,
           evidence_refs=None,status="PROPOSED",version="1"):
    return {"policy_id":policy_id,"name":name,"scope":scope,
            "parameters":parameters or {},
            "evidence_refs":evidence_refs or [],
            "status":status,"version":version}

def policy_change(change_id,policy_ref,from_version,to_version,
                  rationale,evidence_refs,approval_required=True):
    return {"change_id":change_id,"policy_ref":policy_ref,
            "from_version":from_version,"to_version":to_version,
            "rationale":rationale,"evidence_refs":evidence_refs,
            "approval_required":approval_required}
