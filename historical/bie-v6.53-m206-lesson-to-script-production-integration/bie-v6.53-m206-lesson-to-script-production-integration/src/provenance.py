def provenance(script_id, lesson_ids=None, objective_ids=None,
               evidence_ids=None, upstream_artifacts=None):
    return {"script_id":script_id,"lesson_ids":lesson_ids or [],
            "objective_ids":objective_ids or [],
            "evidence_ids":evidence_ids or [],
            "upstream_artifacts":upstream_artifacts or []}

def traceable(p):
    return bool(p["lesson_ids"] and
                (p["objective_ids"] or p["evidence_ids"] or p["upstream_artifacts"]))
