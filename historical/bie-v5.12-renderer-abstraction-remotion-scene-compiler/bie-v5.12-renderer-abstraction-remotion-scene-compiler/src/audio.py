def audio_spec(audio_id,source,start_frame=0,volume=1.0,trim=None):
    return {"audio_id":audio_id,"source":source,"start_frame":start_frame,
            "volume":volume,"trim":trim}

def caption_spec(caption_id,text,start_frame,end_frame,style_ref=None):
    return {"caption_id":caption_id,"text":text,"start_frame":start_frame,
            "end_frame":end_frame,"style_ref":style_ref}
