def timeline(timeline_id,fps=30):
    return {"timeline_id":timeline_id,"fps":fps,"tracks":[],"duration_frames":0}

def add_track(tl,track_id,track_type,items=None):
    tl["tracks"].append({"track_id":track_id,"type":track_type,"items":items or []})
    return tl

def update_duration(tl):
    ends=[i.get("end_frame",0) for t in tl["tracks"] for i in t.get("items",[])]
    tl["duration_frames"]=max(ends) if ends else 0
    return tl
