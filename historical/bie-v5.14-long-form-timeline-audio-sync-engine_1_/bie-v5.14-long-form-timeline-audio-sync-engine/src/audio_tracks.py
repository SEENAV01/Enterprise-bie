def audio_clip(clip_id,source,start_frame,end_frame=None,
               volume=1.0,fade_in=0,fade_out=0):
    return {"clip_id":clip_id,"source":source,"start_frame":start_frame,
            "end_frame":end_frame,"volume":volume,
            "fade_in":fade_in,"fade_out":fade_out}

def music_ducking(duck_id,source_track,narration_track,
                  reduction_db=-12):
    return {"duck_id":duck_id,"source_track":source_track,
            "narration_track":narration_track,"reduction_db":reduction_db}
