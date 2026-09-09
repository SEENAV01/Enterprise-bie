def create_checkpoint(run_id, sequence, state):
    return {"run_id":run_id,"sequence":sequence,"state":state,"status":"COMMITTED"}

def latest_checkpoint(checkpoints, run_id):
    matches=[c for c in checkpoints if c["run_id"]==run_id and c["status"]=="COMMITTED"]
    return max(matches,key=lambda c:c["sequence"]) if matches else None
