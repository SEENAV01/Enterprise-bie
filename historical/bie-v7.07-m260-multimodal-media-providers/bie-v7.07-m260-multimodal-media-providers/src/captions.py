def align_captions(words):
    segments=[]; current=[]
    for word in words:
        current.append(word)
        if word.get("end",0)-current[0].get("start",0)>=2.5 or word.get("text","").endswith((".", "?", "!")):
            segments.append({"start":current[0]["start"],"end":current[-1]["end"],
                             "text":" ".join(w["text"] for w in current)})
            current=[]
    if current:
        segments.append({"start":current[0]["start"],"end":current[-1]["end"],
                         "text":" ".join(w["text"] for w in current)})
    return segments

def validate_captions(segments, duration):
    errors=[]
    last=0
    for s in segments:
        if s["start"]<last or s["end"]<=s["start"] or s["end"]>duration:
            errors.append("CAPTION_TIMING_INVALID")
        last=s["end"]
    return {"valid":not errors,"errors":errors}
