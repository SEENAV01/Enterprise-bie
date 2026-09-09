def coverage_record(target_ref,status,fragment_refs=None,
                    evidence_refs=None,confidence=None,notes=None):
    return {"target_ref":target_ref,"status":status,
            "fragment_refs":fragment_refs or [],
            "evidence_refs":evidence_refs or [],
            "confidence":confidence,"notes":notes}

def coverage_statuses():
    return ["COVERED","PARTIALLY_COVERED","MISSING",
            "CONFLICTING","INSUFFICIENT_EVIDENCE","GENERATE"]
