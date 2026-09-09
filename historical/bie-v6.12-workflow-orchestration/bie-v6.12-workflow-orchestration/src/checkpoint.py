def checkpoint(workflow_id,
                sequence,state,
                created_at):
    return {"workflow_id":workflow_id,
            "sequence":sequence,
            "state":state,
            "created_at":created_at}

def latest(checkpoints):
    return max(checkpoints,
               key=lambda x:x["sequence"]) if checkpoints else None
