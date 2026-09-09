def estimate_duration(text,words_per_minute=130,min_seconds=3):
    words=len(text.split())
    return max(min_seconds,round(words/max(words_per_minute,1)*60,2))

def assign_timing(script_segments,default_wpm=130):
    t=0.0; out=[]
    for s in script_segments:
        dur=estimate_duration(s["text"],default_wpm)
        out.append({"segment_id":s["segment_id"],"start":t,"end":round(t+dur,2),
                    "duration":dur})
        t+=dur
    return out
