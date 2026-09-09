def recover_from_checkpoint(checkpoint):
    if not checkpoint or checkpoint.get("status")!="COMMITTED":
        return {"ok":False,"error":"CHECKPOINT_UNAVAILABLE"}
    return {"ok":True,"run_id":checkpoint["run_id"],
            "sequence":checkpoint["sequence"],"state":checkpoint["state"]}

def replay_events(events, after_sequence=0):
    return [e for e in events if e.get("sequence",0)>after_sequence]
