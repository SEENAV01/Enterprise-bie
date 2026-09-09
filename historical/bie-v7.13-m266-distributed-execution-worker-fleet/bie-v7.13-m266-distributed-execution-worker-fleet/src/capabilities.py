def capabilities():
    return {"worker_registry":True,"heartbeats":True,"capability_matching":True,
            "job_dispatch":True,"leases":True,"fault_recovery":True,
            "worker_isolation":True,"autoscaling_contract":True}
