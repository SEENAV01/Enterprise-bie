def extraction_record(record_id,record_type,source_refs,
                     extraction_method=None,confidence=None):
    return {"record_id":record_id,"record_type":record_type,
            "source_refs":source_refs or [],
            "extraction_method":extraction_method,
            "confidence":confidence}

def provenance_gate(record,minimum_confidence=0.8):
    c=record.get("confidence")
    return {"valid":c is None or c>=minimum_confidence,
            "review_required":c is not None and c<minimum_confidence}
