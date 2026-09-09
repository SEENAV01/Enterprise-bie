def plan_shots(objectives, narration_segments,
               visuals, assets, style_bible, grammar):
    # This is a deterministic planning scaffold.
    # A production planner/LLM can replace the heuristics while preserving the schema.
    shots=[]
    for i,seg in enumerate(narration_segments):
        related=[v for v in visuals if seg["segment_id"] in v.get("narration_cues",[])]
        shots.append({
          "shot_id":f"shot_{i+1}",
          "purpose":seg.get("purpose","EXPLAIN"),
          "narration_segment_ids":[seg["segment_id"]],
          "visual_ids":[v["visual_id"] for v in related],
          "asset_refs":[],
          "composition_id":None,
          "camera":None,
          "timing_source":"NARRATION_TIMELINE"
        })
    return shots
