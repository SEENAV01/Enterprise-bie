def provenance(evidence_id,
               source_type,source_id,
               collected_by,collected_at,
               transformation=None):
    return {"evidence_id":evidence_id,
            "source_type":source_type,
            "source_id":source_id,
            "collected_by":collected_by,
            "collected_at":collected_at,
            "transformation":transformation}

def source_matches(record,source_id):
    return record.get("source_id")==source_id
