def validate_visual(media, requirements):
    errors=[]
    meta=media.get("metadata",{})
    for k,v in requirements.get("metadata",{}).items():
        if meta.get(k)!=v: errors.append(f"VISUAL_METADATA:{k}")
    if not media.get("output_uri"): errors.append("VISUAL_OUTPUT_MISSING")
    return {"valid":not errors,"errors":errors}

def semantic_match(media, expected_concepts):
    concepts=set(media.get("metadata",{}).get("concepts",[]))
    missing=[c for c in expected_concepts if c not in concepts]
    return {"valid":not missing,"missing":missing}
