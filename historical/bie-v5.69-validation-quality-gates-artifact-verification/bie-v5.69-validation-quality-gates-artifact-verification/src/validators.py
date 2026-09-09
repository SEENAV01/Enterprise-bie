from results import check_result

def semantic_validator(artifact,expected_refs):
    actual=set(artifact.get("semantic_refs",[]))
    expected=set(expected_refs)
    return check_result("semantic-refs","SEMANTIC",
        "PASS" if expected<=actual else "FAIL",
        "ERROR" if not expected<=actual else "INFO",
        evidence={"missing":sorted(expected-actual)})

def structural_validator(artifact):
    ok=bool(artifact.get("artifact_id")) and bool(artifact.get("type"))
    return check_result("structure","STRUCTURAL",
        "PASS" if ok else "FAIL","ERROR" if not ok else "INFO")

def dependency_validator(artifact,required_assets):
    actual=set(artifact.get("asset_refs",[]))
    missing=set(required_assets)-actual
    return check_result("dependencies","DEPENDENCY",
        "PASS" if not missing else "FAIL",
        "ERROR" if missing else "INFO",
        evidence={"missing":sorted(missing)})

def accessibility_validator(metadata):
    required=["captions","alt_text","transcript"]
    missing=[x for x in required if not metadata.get(x)]
    return check_result("accessibility","ACCESSIBILITY",
        "PASS" if not missing else "WARN",
        "WARN" if missing else "INFO",
        evidence={"missing":missing})
