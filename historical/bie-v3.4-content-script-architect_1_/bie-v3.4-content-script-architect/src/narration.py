def narration_unit(script_unit, delivery_style="clear_teaching"):
    return {
      "unit_id":script_unit["id"],
      "text":script_unit["text"],
      "delivery_style":delivery_style,
      "emphasis":[],
      "pause_hints":[],
      "audio_sync_anchors":[],
      "evidence_ids":script_unit.get("evidence_ids",[])
    }

def build_narration(script_units):
    return [narration_unit(u) for u in script_units]
