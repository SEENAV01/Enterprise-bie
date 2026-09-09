def overlay(environment,values,
            priority=0):
    return {"environment":environment,
            "values":values,"priority":priority}

def resolve(overlays):
    result={}
    for item in sorted(overlays,key=lambda x:x.get("priority",0)):
        result.update(item.get("values",{}))
    return result
