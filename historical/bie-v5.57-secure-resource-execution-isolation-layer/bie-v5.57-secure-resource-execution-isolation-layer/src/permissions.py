def permission_policy(filesystem="READ_INPUT_WRITE_OUTPUT",
                    network="DENY",process="DENY",
                    device="DENY",secrets="DENY"):
    return {"filesystem":filesystem,"network":network,
            "process":process,"device":device,"secrets":secrets}

def check_permission(policy,operation):
    key=operation.get("resource")
    mode=operation.get("mode")
    allowed=policy.get(key,"DENY")
    return {"allowed": allowed in [mode,"ALLOW","READ_WRITE"],
            "resource":key,"mode":mode}
