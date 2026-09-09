def evidence_bundle(bundle_id,
                   control_id,evidence_refs,
                   period,owner):
    return {"bundle_id":bundle_id,
            "control_id":control_id,
            "evidence_refs":evidence_refs,
            "period":period,
            "owner":owner,
            "status":"ASSEMBLED"}

def complete(bundle):
    out=dict(bundle); out["status"]="COMPLETE"
    return out
