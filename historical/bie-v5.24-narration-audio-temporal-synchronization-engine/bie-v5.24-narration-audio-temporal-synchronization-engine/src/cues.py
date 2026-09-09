def visual_cue(cue_id,target_id,trigger_type,
               start=None,end=None,phrase_ref=None,offset=0):
    return {"cue_id":cue_id,"target_id":target_id,
            "trigger_type":trigger_type,"start":start,"end":end,
            "phrase_ref":phrase_ref,"offset":offset}
