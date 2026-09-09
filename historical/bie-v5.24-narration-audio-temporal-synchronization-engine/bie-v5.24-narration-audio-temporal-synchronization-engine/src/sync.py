def align_cues(phrases,cues):
    by_id={p.get("phrase_id"):p for p in phrases}
    aligned=[]
    for c in cues:
        p=by_id.get(c.get("phrase_ref"))
        item=dict(c)
        if p:
            item["start"]=p["start"]+c.get("offset",0)
            item["end"]=p["end"]+c.get("offset",0)
        aligned.append(item)
    return aligned

def scene_duration(audio_duration,tail_padding=0.2):
    if audio_duration is None or audio_duration<0:
        raise ValueError("INVALID_AUDIO_DURATION")
    return audio_duration+tail_padding
