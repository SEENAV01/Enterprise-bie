from identities import build_identity
from reproducibility import reproducibility_requirements

def compile_governance(manifest,governance=None):
    req=reproducibility_requirements(manifest)
    identity=build_identity(manifest)
    return {"schema_version":"5.56",
            "build_identity":identity,
            "manifest":manifest,
            "governance":governance or {},
            "reproducibility":req,
            "quality_gate":{"valid":req["reproducible"],
                            "errors":req["missing"]}}
