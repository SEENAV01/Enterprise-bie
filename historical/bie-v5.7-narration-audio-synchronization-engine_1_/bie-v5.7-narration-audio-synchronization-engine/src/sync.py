def synchronize(segments, cues, fps=30, words_per_minute=145):
    cursor=0; output=[]
    for s in segments:
        words=segment_timing(s["text"],cursor,fps,words_per_minute)
        duration=words[-1]["end_frame"]-cursor if words else 0
        start=cursor; end=cursor+duration
        output.append({**s,"timing":{"start_frame":start,"end_frame":end},
                       "word_timing":words})
        cursor=end
    resolved=[]
    index={s["segment_id"]:s for s in output}
    for c in cues:
        s=index[c["segment_id"]]
        resolved.append(resolve_cue(c,s["timing"]["start_frame"],
                                    s["timing"]["end_frame"]))
    return {"segments":output,"cues":resolved,"duration_frames":cursor}
