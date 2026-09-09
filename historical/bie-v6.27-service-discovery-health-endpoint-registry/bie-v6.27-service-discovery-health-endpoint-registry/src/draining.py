def drain(endpoint_id,
          reason="DECOMMISSION",
          deadline=None):
    return {"endpoint_id":endpoint_id,
            "reason":reason,
            "deadline":deadline,
            "status":"DRAINING"}

def routable(record):
    return record["status"]!="DRAINING"
