def config(key,value,value_type="string",
           source="default",version=1):
    return {"key":key,"value":value,"type":value_type,
            "source":source,"version":version}

def validate(cfg):
    t=cfg.get("type")
    v=cfg.get("value")
    checks={"string":str,"integer":int,"number":(int,float),
            "boolean":bool,"object":dict,"array":list}
    return t in checks and isinstance(v,checks[t])
