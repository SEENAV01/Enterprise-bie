def parse_progress(event):
    return {"frame":event.get("frame",0),"total_frames":event.get("total_frames",0),
            "percent":round(100*event.get("frame",0)/max(1,event.get("total_frames",1)),2),
            "status":event.get("status","RENDERING")}

def progress_snapshot(events):
    return parse_progress(events[-1]) if events else {"frame":0,"total_frames":0,"percent":0,"status":"QUEUED"}
