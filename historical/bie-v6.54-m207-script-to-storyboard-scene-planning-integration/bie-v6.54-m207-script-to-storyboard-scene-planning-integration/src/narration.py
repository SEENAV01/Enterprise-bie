def narration_link(link_id, scene_id, script_block_ids,
                   start_sec=0, end_sec=None):
    return {"link_id":link_id,"scene_id":scene_id,
            "script_block_ids":script_block_ids,
            "start_sec":start_sec,"end_sec":end_sec}

def valid(item):
    return bool(item["scene_id"] and item["script_block_ids"])
