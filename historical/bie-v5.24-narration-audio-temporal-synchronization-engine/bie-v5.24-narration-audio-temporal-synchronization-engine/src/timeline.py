def temporal_timeline(scene_id,duration_seconds,
                     audio_ref=None,caption_refs=None,cue_refs=None):
    return {"scene_id":scene_id,"duration_seconds":duration_seconds,
            "audio_ref":audio_ref,"caption_refs":caption_refs or [],
            "cue_refs":cue_refs or [],"timing_policy":"AUDIO_DRIVEN"}
