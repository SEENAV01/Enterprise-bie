def evidence(evidence_id, source_id, segment_ids, claim=None, confidence=1.0):
    if not segment_ids:
        raise ValueError("EVIDENCE_REQUIRES_SEGMENTS")
    return {"evidence_id":evidence_id,"source_id":source_id,
            "segment_ids":segment_ids,"claim":claim,"confidence":confidence}

def grounded(record):
    return bool(record["source_id"] and record["segment_ids"])
