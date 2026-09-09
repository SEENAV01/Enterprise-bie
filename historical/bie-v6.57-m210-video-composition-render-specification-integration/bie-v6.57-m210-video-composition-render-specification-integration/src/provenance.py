def provenance(composition_id, storyboard_ids=None,
               asset_ids=None, audio_ids=None, scene_ids=None,
               upstream_artifacts=None):
    return {"composition_id":composition_id,
            "storyboard_ids":storyboard_ids or [],
            "asset_ids":asset_ids or [],
            "audio_ids":audio_ids or [],
            "scene_ids":scene_ids or [],
            "upstream_artifacts":upstream_artifacts or []}

def traceable(p):
    return bool(p["storyboard_ids"] and
                (p["asset_ids"] or p["audio_ids"] or
                 p["scene_ids"] or p["upstream_artifacts"]))
