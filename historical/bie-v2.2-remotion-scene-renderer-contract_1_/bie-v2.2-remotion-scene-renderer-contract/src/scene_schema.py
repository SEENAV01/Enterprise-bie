SCENE_TYPES=[
    "definition","causal_explanation","process_animation",
    "derivation","application","comparison","diagram_explanation",
    "worked_example","checkpoint","recap"
]

VISUAL_TYPES=[
    "text","diagram","equation","chart","table","timeline",
    "process","simulation","real_world","mixed"
]

def validate_scene(s):
    errors=[]
    required=["scene_id","type","duration_ms","objective","visual","narration","evidence_refs"]
    for k in required:
        if k not in s: errors.append("missing:"+k)
    if s.get("type") not in SCENE_TYPES: errors.append("invalid:type")
    if s.get("visual",{}).get("type") not in VISUAL_TYPES: errors.append("invalid:visual.type")
    if not isinstance(s.get("duration_ms"),int) or s.get("duration_ms",0)<=0:
        errors.append("invalid:duration_ms")
    return errors
