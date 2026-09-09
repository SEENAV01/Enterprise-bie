def word_timing(word,start,end,index=None):
    return {"word":word,"start":start,"end":end,"index":index}

def phrase_timing(text,start,end,words=None):
    return {"text":text,"start":start,"end":end,"words":words or []}

def validate_timings(items):
    errors=[]
    previous=-1
    for x in items:
        if x["start"]<previous: errors.append("NON_MONOTONIC_TIMING")
        if x["end"]<x["start"]: errors.append("INVALID_RANGE")
        previous=x["start"]
    return {"valid":not errors,"errors":errors}
