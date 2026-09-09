def validate_assets(required,available):
    available=set(available)
    missing=[x for x in required if x not in available]
    return {"valid":not missing,"missing":missing}

def validate_audio_refs(required,available):
    available=set(available)
    missing=[x for x in required if x not in available]
    return {"valid":not missing,"missing":missing}
