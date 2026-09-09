def caption(caption_id,text,start,end,segment_ref=None,
            style_ref=None):
    return {"caption_id":caption_id,"text":text,"start":start,
            "end":end,"segment_ref":segment_ref,"style_ref":style_ref}

def caption_track(track_id,captions,language="en"):
    return {"track_id":track_id,"captions":captions,
            "language":language}
