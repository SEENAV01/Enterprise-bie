def normalize_transcript(raw):
    # Accept either a plain transcript or word-level timing.
    if isinstance(raw,str):
        return {"text":raw,"words":[]}
    return {
      "text":raw.get("text",""),
      "words":raw.get("words",[]),
      "duration_s":raw.get("duration_s")
    }

def sentence_ranges(text):
    import re
    return [(m.start(),m.end()) for m in re.finditer(r'[^.!?]+[.!?]',text)]
