def anti_entropy(node_id,peer_id,
                 cursor=None):
    return {"node_id":node_id,"peer_id":peer_id,
            "cursor":cursor,"status":"RUNNING"}

def complete(record):
    out=dict(record); out["status"]="COMPLETED"; return out
