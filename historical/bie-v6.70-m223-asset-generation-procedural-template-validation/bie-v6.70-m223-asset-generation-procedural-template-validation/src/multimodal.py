def validate_modalities(asset,required):
    available=set(asset.get("modalities",[]))
    checks={m:m in available for m in required}
    return {"checks":checks,"passed":all(checks.values())}

def validate_semantics(asset,required_tags):
    tags=set(asset.get("tags",[]))
    return {"missing":[t for t in required_tags if t not in tags],
            "passed":all(t in tags for t in required_tags)}
