VISUAL_MODES=[
"TEXT","DIAGRAM","EQUATION","PROCESS","CHART","TABLE","MAP",
"EXAMPLE","COMPARISON","HIGHLIGHT","CAMERA_EXPLANATION"
]

def visual_instruction(script_unit):
    intent=script_unit.get("visual_intent")
    typ=script_unit.get("type")
    mode="TEXT"
    if intent:
        if "equation" in intent: mode="EQUATION"
        elif "process" in intent: mode="PROCESS"
        elif "visual" in intent: mode="DIAGRAM"
        elif "example" in intent: mode="EXAMPLE"
        elif "application" in typ.lower(): mode="EXAMPLE"
    return {
      "unit_id":script_unit["id"],
      "mode":mode,
      "objective":script_unit["objective"],
      "visual_intent":intent,
      "source_asset_refs":[],
      "animation_requirements":[],
      "must_preserve":[] 
    }

def build_visual_instructions(script_units):
    return [visual_instruction(u) for u in script_units]
