def estimate_load(scene):
    n=len(scene.get("objects",[]))
    simultaneous=sum(1 for o in scene.get("objects",[])
                     if o.get("animated",False))
    text_chars=sum(len(str(o.get("content",""))) for o in scene.get("objects",[])
                   if o.get("kind")=="TEXT")
    load=0.2*n+0.35*simultaneous+0.002*text_chars
    return min(1.0,load)

def recommend(scene):
    load=estimate_load(scene)
    if load>=0.8:
        return {"level":"HIGH","action":"SEQUENCE_OR_SIMPLIFY"}
    if load>=0.55:
        return {"level":"MEDIUM","action":"REDUCE_SIMULTANEOUS_ELEMENTS"}
    return {"level":"LOW","action":"OK"}
