def provenance(manifest_id, storyboard_ids=None,
               scene_ids=None, evidence_ids=None,
               upstream_artifacts=None):
    return {
        "manifest_id": manifest_id,
        "storyboard_ids": storyboard_ids or [],
        "scene_ids": scene_ids or [],
        "evidence_ids": evidence_ids or [],
        "upstream_artifacts": upstream_artifacts or []
    }

def traceable(p):
    return bool(p["storyboard_ids"] and
                (p["scene_ids"] or p["evidence_ids"] or
                 p["upstream_artifacts"]))
