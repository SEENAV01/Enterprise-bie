def drain(instance_id,started_at,
          deadline=None):
    return {"instance_id":instance_id,
            "started_at":started_at,
            "deadline":deadline,
            "status":"DRAINING"}

def can_receive_new_traffic(record):
    return record.get("status")!="DRAINING"
