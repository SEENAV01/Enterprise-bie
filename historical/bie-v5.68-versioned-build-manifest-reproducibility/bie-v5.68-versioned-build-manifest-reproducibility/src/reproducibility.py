def compare_manifests(a,b):
    fields=["inputs","assets","ir_version","generator",
            "renderer","dependencies","config","policies",
            "environment","seeds"]
    differences={}
    for f in fields:
        if a.get(f)!=b.get(f):
            differences[f]={"a":a.get(f),"b":b.get(f)}
    return {"reproducible_inputs_match":not differences,
            "differences":differences}

def reproducibility_gate(manifest,required=None):
    required=required or ["inputs","assets","ir_version",
                           "generator","renderer","dependencies"]
    missing=[f for f in required if not manifest.get(f)]
    return {"valid":not missing,"missing":missing}
