def consistency_policy(mode,
                      allow_partial=False,
                      compensation_required=True):
    return {"mode":mode,
            "allow_partial":allow_partial,
            "compensation_required":compensation_required}

def terminal(status):
    return status in {"COMPLETED","COMPENSATED",
                      "FAILED","PARTIAL"}
