def build_manifest(build_id,nodes,artifacts=None,
                  tool_versions=None,source_refs=None):
    return {"build_id":build_id,"nodes":nodes,
            "artifacts":artifacts or {},
            "tool_versions":tool_versions or {},
            "source_refs":source_refs or []}
