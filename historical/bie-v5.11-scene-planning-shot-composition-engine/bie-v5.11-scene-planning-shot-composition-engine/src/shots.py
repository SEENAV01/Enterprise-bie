def shot(shot_id, purpose, narration_segment_ids=None,
         visual_ids=None, asset_refs=None):
    return {
      "shot_id":shot_id,
      "purpose":purpose,
      "narration_segment_ids":narration_segment_ids or [],
      "visual_ids":visual_ids or [],
      "asset_refs":asset_refs or [],
      "timing":{"start_frame":None,"end_frame":None}
    }

def shot_beat(beat_id, shot_id, trigger, action, target_ids=None):
    return {
      "beat_id":beat_id,"shot_id":shot_id,"trigger":trigger,
      "action":action,"target_ids":target_ids or []
    }
