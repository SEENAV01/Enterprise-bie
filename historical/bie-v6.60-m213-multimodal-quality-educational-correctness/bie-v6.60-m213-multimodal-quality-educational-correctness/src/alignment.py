def alignment_record(record_id, script_ref, scene_ref,
                     asset_refs=None, narration_ref=None,
                     caption_refs=None, score=1.0):
    if not 0 <= score <= 1:
        raise ValueError("INVALID_ALIGNMENT_SCORE")
    return {"record_id":record_id,"script_ref":script_ref,
            "scene_ref":scene_ref,"asset_refs":asset_refs or [],
            "narration_ref":narration_ref,
            "caption_refs":caption_refs or [],"score":score}

def valid(a):
    return bool(a["record_id"] and a["script_ref"] and a["scene_ref"])
