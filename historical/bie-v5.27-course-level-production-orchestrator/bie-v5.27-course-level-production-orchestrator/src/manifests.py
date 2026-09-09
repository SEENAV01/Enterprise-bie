def artifact_manifest(artifact_id,kind,path,fingerprint,
                     source_refs=None,dependencies=None):
    return {"artifact_id":artifact_id,"kind":kind,"path":path,
            "fingerprint":fingerprint,"source_refs":source_refs or [],
            "dependencies":dependencies or []}
