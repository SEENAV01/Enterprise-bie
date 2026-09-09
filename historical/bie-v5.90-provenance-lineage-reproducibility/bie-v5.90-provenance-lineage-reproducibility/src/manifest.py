def manifest(artifact_id,artifact_hash,inputs=None,
             model=None,prompt=None,config=None,code=None,
             dependencies=None,environment=None):
    return {
      "artifact_id":artifact_id,"artifact_hash":artifact_hash,
      "inputs":inputs or [],"model":model,"prompt":prompt,
      "config":config,"code":code,
      "dependencies":dependencies or [],
      "environment":environment or {},
      "schema_version":"5.90"
    }

def immutable(m):
    out=dict(m); out["immutable"]=True; return out
