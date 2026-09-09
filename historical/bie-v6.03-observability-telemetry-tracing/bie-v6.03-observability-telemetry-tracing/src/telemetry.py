def execution_telemetry(task_id,worker_id,
                       status,start,end=None,
                       cost=None,usage=None):
    return {"task_id":task_id,"worker_id":worker_id,
            "status":status,"start":start,"end":end,
            "cost":cost,"usage":usage}

def latency(t):
    if t.get("end") is None: return None
    return t["end"]-t["start"]
