def sync_anchor(anchor_id,source_type,source_ref,target_type,
                target_ref,offset=0.0):
    return {"anchor_id":anchor_id,"source_type":source_type,
            "source_ref":source_ref,"target_type":target_type,
            "target_ref":target_ref,"offset":offset}

def sync_types():
    return ["WORD","PHRASE","SEGMENT","AUDIO_EVENT","VISUAL_EVENT",
            "ANIMATION_STATE","INTERACTION"]
