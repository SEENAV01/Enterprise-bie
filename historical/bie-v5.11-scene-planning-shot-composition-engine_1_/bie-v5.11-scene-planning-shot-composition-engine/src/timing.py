def assign_shot_timing(shots, narration_segments):
    index={s["segment_id"]:s for s in narration_segments}
    result=[]
    for sh in shots:
        starts=[]; ends=[]
        for sid in sh.get("narration_segment_ids",[]):
            if sid in index:
                t=index[sid].get("timing",{})
                if t.get("start_frame") is not None: starts.append(t["start_frame"])
                if t.get("end_frame") is not None: ends.append(t["end_frame"])
        result.append({**sh,"timing":{
          "start_frame":min(starts) if starts else None,
          "end_frame":max(ends) if ends else None
        }})
    return result
