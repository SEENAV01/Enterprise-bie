def command(command_id,command_type,
            payload_ref,
            tenant_id=None,
            correlation_id=None):
    return {"command_id":command_id,
            "command_type":command_type,
            "payload_ref":payload_ref,
            "tenant_id":tenant_id,
            "correlation_id":correlation_id,
            "status":"READY"}

def accepted(record):
    out=dict(record); out["status"]="ACCEPTED"; return out
