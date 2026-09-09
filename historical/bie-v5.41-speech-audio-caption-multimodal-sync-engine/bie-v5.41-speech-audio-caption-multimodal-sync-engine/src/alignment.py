def word_alignment(segment_id,words):
    return {"segment_id":segment_id,"words":words}

def word(text,start,end,index=None):
    return {"text":text,"start":start,"end":end,"index":index}

def validate_alignment(alignment):
    errors=[]
    prev=0.0
    for w in alignment.get("words",[]):
        if w.get("start",0)<prev or w.get("end",0)<w.get("start",0):
            errors.append("INVALID_WORD_ALIGNMENT")
        prev=w.get("end",prev)
    return sorted(set(errors))
