def build_manifest(build_id,inputs=None,assets=None,
                  ir_version=None,generator=None,renderer=None,
                  dependencies=None,config=None,policies=None,
                  environment=None,seeds=None):
    return {
      "manifest_version":"1",
      "build_id":build_id,
      "inputs":inputs or {},
      "assets":assets or [],
      "ir_version":ir_version,
      "generator":generator or {},
      "renderer":renderer or {},
      "dependencies":dependencies or {},
      "config":config or {},
      "policies":policies or {},
      "environment":environment or {},
      "seeds":seeds or {}
    }
