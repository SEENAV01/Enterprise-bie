def verify_provenance(artifact,expected_source_refs=None):
    expected=set(expected_source_refs or [])
    actual=set(artifact.get("source_refs",[]))
    return {"valid":expected.issubset(actual),
            "missing":sorted(expected-actual)}

def verify_generated_labels(artifact):
    if artifact.get("generated_refs") and not artifact.get("generated_label"):
        return {"valid":False,"error":"GENERATED_CONTENT_UNLABELED"}
    return {"valid":True}
