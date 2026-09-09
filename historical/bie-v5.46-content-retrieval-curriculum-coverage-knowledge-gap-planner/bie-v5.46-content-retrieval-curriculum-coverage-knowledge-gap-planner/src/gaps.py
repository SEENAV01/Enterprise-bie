def knowledge_gap(gap_id,target_ref,gap_type,status,
                evidence_refs=None,priority=None,reason=None):
    return {"gap_id":gap_id,"target_ref":target_ref,
            "gap_type":gap_type,"status":status,
            "evidence_refs":evidence_refs or [],
            "priority":priority,"reason":reason}

def gap_types():
    return ["CONTENT_MISSING","DEPTH_MISSING","PREREQUISITE_MISSING",
            "SOURCE_CONFLICT","REPRESENTATION_MISSING",
            "EXAMPLE_MISSING","ASSESSMENT_MISSING"]
