from time import time
def event(event_type, run_id, payload=None, level="INFO"):
    return {"ts":time(),"type":event_type,"run_id":run_id,"level":level,
            "payload":payload or {}}

def normalize_event(e):
    return {"ts":e["ts"],"type":e["type"],"run_id":e["run_id"],
            "level":e["level"],"payload":e.get("payload",{})}
