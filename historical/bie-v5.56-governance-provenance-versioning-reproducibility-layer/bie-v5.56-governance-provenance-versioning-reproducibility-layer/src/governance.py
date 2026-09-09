def approval(approval_id,target_ref,actor,decision,
             timestamp=None,reason=None):
    return {"approval_id":approval_id,"target_ref":target_ref,
            "actor":actor,"decision":decision,
            "timestamp":timestamp,"reason":reason}

def governance_record(build_ref,approvals=None,policy_pins=None,
                      release_state="DRAFT"):
    return {"build_ref":build_ref,"approvals":approvals or [],
            "policy_pins":policy_pins or [],
            "release_state":release_state}
