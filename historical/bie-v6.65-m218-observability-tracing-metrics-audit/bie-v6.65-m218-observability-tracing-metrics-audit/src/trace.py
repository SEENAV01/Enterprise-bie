import time, uuid
def trace_id(): return uuid.uuid4().hex
def span(span_id,name,parent_id=None,start=None,end=None,
         attributes=None,status="OK"):
    return {"span_id":span_id,"name":name,"parent_id":parent_id,
            "start":start if start is not None else time.time(),
            "end":end,"attributes":attributes or {},"status":status}
def duration(s):
    return None if s["end"] is None else max(0,s["end"]-s["start"])
