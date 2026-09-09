from retention import retention_action
from gc import deletion_decision

def compile_lifecycle(artifact,age_seconds,policy,
                      holds=None,dependencies=None):
    action=retention_action(age_seconds,policy)
    holds=holds or []
    dependencies=dependencies or {}
    if action=="DELETE":
        decision=deletion_decision(
            artifact["artifact_id"],holds,dependencies)
        if decision!="ELIGIBLE": action="RETAIN"
    return {"schema_version":"5.84",
            "artifact_id":artifact["artifact_id"],
            "action":action,
            "quality_gate":{"valid":True,"errors":[]}}
