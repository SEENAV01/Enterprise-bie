def queue_state(queue_id,items=None,leases=None,
                completed=None,failed=None):
    return {"queue_id":queue_id,"items":items or [],
            "leases":leases or {},"completed":completed or [],
            "failed":failed or []}

def enqueue(state,job):
    state=dict(state)
    state["items"]=list(state.get("items",[]))+[job]
    return state
