def policy_version(policy_id,version,parameters=None,
                  objective="MAXIMIZE_LEARNING_OUTCOME"):
    return {"policy_id":policy_id,"version":version,
            "parameters":parameters or {},"objective":objective}

def policy_update(proposed,current,minimum_evidence=1):
    if proposed.get("evidence_count",0)<minimum_evidence:
        return {"accepted":False,"reason":"INSUFFICIENT_EVIDENCE",
                "policy":current}
    return {"accepted":True,"reason":"EVIDENCE_THRESHOLD_MET",
            "policy":proposed}
