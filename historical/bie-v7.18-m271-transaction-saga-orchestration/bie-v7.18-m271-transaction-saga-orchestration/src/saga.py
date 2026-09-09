def create_saga(saga_id, steps, context=None):
    return {"saga_id":saga_id,"steps":steps,"context":context or {},
            "completed":[],"compensated":[],"status":"RUNNING"}

def next_step(saga):
    for step in saga["steps"]:
        if step["id"] not in saga["completed"] and step["id"] not in saga["compensated"]:
            return step
    return None
