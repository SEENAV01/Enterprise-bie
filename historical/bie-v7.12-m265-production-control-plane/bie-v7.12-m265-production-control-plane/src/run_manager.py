from states import valid_transition

def create_run(run_id, scope, owner="system"):
    return {"run_id":run_id,"scope":scope,"owner":owner,"state":"CREATED","revision":0}

def transition(run,target,actor="system",reason=None):
    if not valid_transition(run["state"],target):
        return {"ok":False,"error":"INVALID_STATE_TRANSITION","run":run}
    run["state"]=target; run["revision"]+=1
    run["last_transition"]={"actor":actor,"from":run["state"] if False else None,
                            "to":target,"reason":reason}
    return {"ok":True,"run":run}
