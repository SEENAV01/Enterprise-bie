def provenance(audio_id, script_ids=None, scene_ids=None,
               evidence_ids=None, upstream_artifacts=None):
    return {"audio_id":audio_id,"script_ids":script_ids or [],
            "scene_ids":scene_ids or [],"evidence_ids":evidence_ids or [],
            "upstream_artifacts":upstream_artifacts or []}

def traceable(p):
    return bool(p["script_ids"] and
                (p["scene_ids"] or p["evidence_ids"] or p["upstream_artifacts"]))
