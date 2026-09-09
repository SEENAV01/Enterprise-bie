def build_scene_spec(intent,asset,equation,narration):
    return {"scene_id":f"scene-{intent['concept_id']}",
            "concept_id":intent["concept_id"],
            "visual":{"intent":intent["visual_intent"],"asset":asset},
            "equation":{"intent":intent["equation_intent"],"render":equation},
            "narration":narration}

def validate_scene_spec(spec):
    errors=[]
    if not spec.get("visual",{}).get("asset"): errors.append("MISSING_VISUAL_ASSET")
    if spec.get("equation",{}).get("intent") and not spec.get("equation",{}).get("render"):
        errors.append("MISSING_EQUATION_RENDER")
    if not spec.get("narration"): errors.append("MISSING_NARRATION")
    return {"valid":not errors,"errors":errors}
