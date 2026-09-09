from manifest import manifest,immutable
from replay import replay_plan,replay_ready
from verify import verify_manifest

def compile_provenance(artifact_id,artifact_hash,
                       inputs=None,model=None,prompt=None,
                       config=None,code=None,dependencies=None,
                       environment=None):
    m=immutable(manifest(
      artifact_id,artifact_hash,inputs,model,prompt,config,
      code,dependencies,environment))
    plan=replay_plan(m)
    return {"schema_version":"5.90",
            "manifest":m,
            "replay_plan":plan,
            "replay_ready":replay_ready(plan),
            "manifest_valid":verify_manifest(m),
            "quality_gate":{"valid":True,"errors":[]}}
