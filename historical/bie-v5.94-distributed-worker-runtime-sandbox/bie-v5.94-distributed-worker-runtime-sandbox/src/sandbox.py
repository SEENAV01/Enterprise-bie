def sandbox(sandbox_id,image=None,limits=None,
            mounts=None,network="DENY"):
    return {"sandbox_id":sandbox_id,"image":image,
            "limits":limits or {},"mounts":mounts or [],
            "network":network,"status":"READY"}

def validate(sandbox_record):
    return (sandbox_record.get("network") in {"DENY","ALLOWLIST"}
            and bool(sandbox_record.get("sandbox_id")))
