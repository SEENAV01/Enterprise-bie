def sync_point(sync_id, scene_id, narration_segment_id=None,
               asset_ids=None, start_sec=0, end_sec=None):
    return {"sync_id":sync_id,"scene_id":scene_id,
            "narration_segment_id":narration_segment_id,
            "asset_ids":asset_ids or [],
            "start_sec":start_sec,"end_sec":end_sec}

def valid(s):
    return bool(s["sync_id"] and s["scene_id"])

def overlaps(a,b):
    a_end=a.get("end_sec")
    b_end=b.get("end_sec")
    if a_end is None or b_end is None:
        return False
    return max(a["start_sec"],b["start_sec"]) < min(a_end,b_end)
