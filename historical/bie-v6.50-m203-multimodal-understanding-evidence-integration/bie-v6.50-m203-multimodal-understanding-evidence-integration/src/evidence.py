def multimodal_evidence(evidence_id, source_id, record_ids,
                       claim=None, confidence=1.0):
    if not record_ids:
        raise ValueError("EVIDENCE_REQUIRES_RECORDS")
    return {
        "evidence_id": evidence_id, "source_id": source_id,
        "record_ids": record_ids, "claim": claim,
        "confidence": confidence
    }

def grounded(record):
    return bool(record["source_id"] and record["record_ids"])
