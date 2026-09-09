def provenance_claim(claim_id, subject_id,
                     source, method=None, timestamp=None,
                     confidence=None):
    return {"claim_id":claim_id,"subject_id":subject_id,
            "source":source,"method":method,
            "timestamp":timestamp,"confidence":confidence}

def attributed(record):
    return bool(record["source"])
