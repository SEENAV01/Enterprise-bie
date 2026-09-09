def visual_cue(cue_id, segment_id, trigger,
               target_ids, offset_frames=0, duration_frames=None):
    return {
      "cue_id":cue_id,
      "segment_id":segment_id,
      "trigger":trigger,
      "target_ids":target_ids,
      "offset_frames":offset_frames,
      "duration_frames":duration_frames
    }

def resolve_cue(cue, segment_start, segment_end):
    return {
      **cue,
      "frame":segment_start+cue.get("offset_frames",0),
      "end_frame":(
        segment_start+cue.get("offset_frames",0)+cue["duration_frames"]
        if cue.get("duration_frames") is not None else segment_end
      )
    }
