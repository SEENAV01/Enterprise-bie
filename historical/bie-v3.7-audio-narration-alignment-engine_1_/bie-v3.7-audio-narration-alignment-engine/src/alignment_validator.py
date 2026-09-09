def validate_alignment(words, narration_text):
    expected=len(narration_text.split())
    errors=[]
    if len(words)!=expected: errors.append("WORD_COUNT_MISMATCH")
    last=-1
    for w in words:
        if w["start"] is None or w["end"] is None: errors.append("MISSING_TIMESTAMP")
        if w["start"] is not None and w["end"] is not None:
            if w["end"]<w["start"]: errors.append("NEGATIVE_DURATION")
            if w["start"]<last: errors.append("NON_MONOTONIC_TIMELINE")
            last=w["end"]
    return {"valid":not errors,"errors":errors}
