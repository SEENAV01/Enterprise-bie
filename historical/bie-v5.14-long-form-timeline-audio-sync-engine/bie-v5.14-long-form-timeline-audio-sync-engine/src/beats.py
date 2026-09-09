def visual_beat(beat_id,segment_id,trigger,start_frame,
               end_frame=None,action=None,target_ids=None):
    return {"beat_id":beat_id,"segment_id":segment_id,"trigger":trigger,
            "start_frame":start_frame,"end_frame":end_frame,
            "action":action or "HOLD","target_ids":target_ids or []}

def emphasis_beat(beat_id,segment_id,phrase,start_frame,end_frame):
    return {"beat_id":beat_id,"segment_id":segment_id,"trigger":"EMPHASIS",
            "phrase":phrase,"start_frame":start_frame,"end_frame":end_frame}
