def caption(caption_id,text,start_frame,end_frame,
            words=None,style_ref=None):
    return {"caption_id":caption_id,"text":text,
            "start_frame":start_frame,"end_frame":end_frame,
            "words":words or [],"style_ref":style_ref}
