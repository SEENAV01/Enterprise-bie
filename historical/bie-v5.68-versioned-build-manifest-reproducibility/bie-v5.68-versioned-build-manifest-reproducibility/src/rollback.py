def release_record(build_id,artifact_refs,
                  manifest_digest_value,status="RELEASED"):
    return {"build_id":build_id,
            "artifact_refs":artifact_refs,
            "manifest_digest":manifest_digest_value,
            "status":status}

def rollback_target(releases,build_id):
    for r in reversed(releases):
        if r.get("build_id")==build_id:
            return r
    return None
