from script_blocks import ordered

def script(script_id, lesson_id, blocks, tone="clear",
           audience="learner", target_duration_sec=None):
    return {"script_id":script_id,"lesson_id":lesson_id,
            "blocks":ordered(blocks),"tone":tone,
            "audience":audience,
            "target_duration_sec":target_duration_sec}

def valid(item):
    return bool(item["script_id"] and item["lesson_id"] and item["blocks"])
