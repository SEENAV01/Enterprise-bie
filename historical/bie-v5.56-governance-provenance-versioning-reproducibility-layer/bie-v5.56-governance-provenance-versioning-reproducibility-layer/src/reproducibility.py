def reproducibility_requirements(manifest):
    missing=[]
    for key in ["source_pins","model_pins","tool_pins","policy_pins"]:
        if not manifest.get(key): missing.append(key)
    if not manifest.get("environment"):
        missing.append("environment")
    return {"reproducible":not missing,"missing":missing}

def compare_manifests(a,b):
    keys=["artifact_refs","source_pins","model_pins","tool_pins",
          "policy_pins","experiment_pins","environment"]
    differences={}
    for k in keys:
        if a.get(k)!=b.get(k):
            differences[k]={"a":a.get(k),"b":b.get(k)}
    return {"identical":not differences,"differences":differences}
