def evidence(evidence_id,evidence_type,
             source,created_at,
             content_ref=None,
             integrity=None):
    return {"evidence_id":evidence_id,
            "evidence_type":evidence_type,
            "source":source,
            "created_at":created_at,
            "content_ref":content_ref,
            "integrity":integrity,
            "status":"COLLECTED"}

def verify(record,expected_hash=None):
    if expected_hash is None:
        return record.get("status")=="COLLECTED"
    return record.get("integrity",{}).get("event_hash")==expected_hash
