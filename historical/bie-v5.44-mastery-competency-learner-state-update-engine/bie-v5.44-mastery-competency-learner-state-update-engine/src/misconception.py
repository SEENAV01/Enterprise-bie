def misconception_risk(ref,probability=None,evidence_refs=None,
                     last_seen=None,status="ACTIVE"):
    return {"ref":ref,"probability":probability,
            "evidence_refs":evidence_refs or [],
            "last_seen":last_seen,"status":status}
