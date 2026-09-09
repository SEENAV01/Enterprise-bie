def focus_plan(narration_segment, visual_ids):
    purpose=narration_segment.get("purpose","EXPLAIN")
    if purpose in ("DEFINE","RESULT"):
        priority="PRIMARY_RESULT"
    elif purpose in ("COMPARE","CONTRAST"):
        priority="COMPARISON"
    else:
        priority="NARRATION_TARGET"
    return {
      "segment_id":narration_segment["segment_id"],
      "priority":priority,
      "visual_ids":visual_ids
    }
