def caption(caption_id,text,start,end,style=None):
    return {"caption_id":caption_id,"text":text,"start":start,
            "end":end,"style":style or {}}

def captions_from_phrases(phrases):
    return [caption("cap-"+str(i),p["text"],p["start"],p["end"])
            for i,p in enumerate(phrases)]
