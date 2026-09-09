def validate_compilation(result):
    errors=[]
    ir=result.get("ir",{})
    if ir.get("duration_mode")!="AUDIO_DRIVEN": errors.append("TIMING_NOT_AUDIO_DRIVEN")
    keys=[x.get("key") for x in ir.get("layers",[])]
    if len(keys)!=len(set(keys)): errors.append("DUPLICATE_LAYER_KEYS")
    if "component_source" not in result: errors.append("NO_COMPONENT_SOURCE")
    return {"valid":not errors,"errors":errors}
