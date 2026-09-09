def sandbox_spec(sandbox_id,limits,network,
                 filesystem,process,environment=None):
    return {"sandbox_id":sandbox_id,"limits":limits,
            "network":network,"filesystem":filesystem,
            "process":process,"environment":environment or {},
            "output_contract":{"mode":"ARTIFACT_ONLY"}}

def sandbox_gate(spec):
    required=["limits","network","filesystem","process"]
    missing=[x for x in required if not spec.get(x)]
    return {"valid":not missing,"missing":missing}
