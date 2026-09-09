def orphan_candidates(artifacts,referenced_ids):
    return [a for a in artifacts
            if a.get("artifact_id") not in referenced_ids]

def deletion_decision(artifact_id,holds,dependencies):
    if deletion_blocked(artifact_id,holds):
        return "BLOCKED_BY_HOLD"
    if dependencies.get(artifact_id):
        return "BLOCKED_BY_DEPENDENCY"
    return "ELIGIBLE"
