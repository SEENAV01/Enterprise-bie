from digest import manifest_digest
from reproducibility import reproducibility_gate

def compile_manifest(manifest):
    gate=reproducibility_gate(manifest)
    return {"schema_version":"5.68",
            "manifest":manifest,
            "manifest_digest":manifest_digest(manifest),
            "reproducibility":gate,
            "quality_gate":{"valid":gate["valid"],
                            "errors":gate["missing"]}}
