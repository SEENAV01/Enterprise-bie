def evidence_map(scene_id, evidence_ids=None, source_record_ids=None):
    return {"scene_id":scene_id,
            "evidence_ids":evidence_ids or [],
            "source_record_ids":source_record_ids or []}

def grounded(item):
    return bool(item["evidence_ids"] or item["source_record_ids"])
