def pause(run): return {"action":"PAUSE","target":run["run_id"]}
def resume(run): return {"action":"RESUME","target":run["run_id"]}
def cancel(run,reason="OPERATOR_REQUEST"): return {"action":"CANCEL","target":run["run_id"],"reason":reason}
def command_allowed(state,action):
    return {"PAUSE":state=="RUNNING","RESUME":state=="PAUSED",
            "CANCEL":state in {"CREATED","QUEUED","RUNNING","PAUSED","FAILED"}}.get(action,False)
