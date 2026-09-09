def checkpoint(task_id,sequence,state,
               outputs=None):
    return {"task_id":task_id,"sequence":sequence,
            "state":state,"outputs":outputs or []}

def latest(checkpoints):
    return max(checkpoints,key=lambda x:x["sequence"]) if checkpoints else None
