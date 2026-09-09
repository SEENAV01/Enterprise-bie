def replay_plan(topic_name,
                start_position,
                end_position,
                target=None):
    return {"topic":topic_name,
            "start_position":start_position,
            "end_position":end_position,
            "target":target,
            "status":"PLANNED"}

def start(plan):
    out=dict(plan); out["status"]="RUNNING"
    return out
