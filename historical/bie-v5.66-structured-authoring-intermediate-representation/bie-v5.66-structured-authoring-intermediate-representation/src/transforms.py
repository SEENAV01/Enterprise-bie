def transform(name,version,parameters=None):
    return {"name":name,"version":version,
            "parameters":parameters or {}}

def transform_pipeline(ir,transforms):
    out=ir
    history=[]
    for t in transforms:
        history.append(t)
    return {"ir":out,"applied_transforms":history}
