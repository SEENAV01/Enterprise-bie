SUPPORTED_SCENE_TYPES = {
    "TITLE","EXPLANATION","DIAGRAM","ANIMATION","EXAMPLE",
    "DEMONSTRATION","QUESTION","SUMMARY","TRANSITION"
}

def scene(scene_id, scene_type, purpose, script_block_ids,
          objective_ids=None, duration_sec=None, order=0):
    if scene_type not in SUPPORTED_SCENE_TYPES:
        raise ValueError("UNSUPPORTED_SCENE_TYPE")
    if not script_block_ids:
        raise ValueError("SCENE_REQUIRES_SCRIPT_BLOCKS")
    return {"scene_id":scene_id,"scene_type":scene_type,"purpose":purpose,
            "script_block_ids":script_block_ids,
            "objective_ids":objective_ids or [],
            "duration_sec":duration_sec,"order":order}

def valid(item):
    return bool(item["scene_id"] and item["purpose"] and item["script_block_ids"])

def ordered(scenes):
    return sorted(scenes,key=lambda x:x["order"])
