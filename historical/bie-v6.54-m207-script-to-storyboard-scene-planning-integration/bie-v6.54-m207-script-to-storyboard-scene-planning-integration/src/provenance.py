def provenance(storyboard_id, script_ids=None, lesson_ids=None,
               evidence_ids=None, upstream_artifacts=None):
    return {"storyboard_id":storyboard_id,"script_ids":script_ids or [],
            "lesson_ids":lesson_ids or [],
            "evidence_ids":evidence_ids or [],
            "upstream_artifacts":upstream_artifacts or []}

def traceable(p):
    return bool(p["script_ids"] and
                (p["evidence_ids"] or p["upstream_artifacts"]))
