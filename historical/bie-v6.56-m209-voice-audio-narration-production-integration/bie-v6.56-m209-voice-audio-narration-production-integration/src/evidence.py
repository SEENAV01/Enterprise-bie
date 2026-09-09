def evidence_binding(narration_segment_id, evidence_ids=None,
                    source_record_ids=None):
    return {"narration_segment_id":narration_segment_id,
            "evidence_ids":evidence_ids or [],
            "source_record_ids":source_record_ids or []}

def grounded(item):
    return bool(item["evidence_ids"] or item["source_record_ids"])
