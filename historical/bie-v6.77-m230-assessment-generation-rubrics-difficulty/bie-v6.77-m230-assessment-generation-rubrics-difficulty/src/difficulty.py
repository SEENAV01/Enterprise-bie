LEVELS=["EASY","MEDIUM","HARD"]
def calibrate_difficulty(bloom,steps=1,abstraction=1):
    base={"REMEMBER":0,"UNDERSTAND":0,"APPLY":1,"ANALYZE":1,
          "EVALUATE":2,"CREATE":2}.get(bloom,1)
    value=base+(1 if steps>=3 else 0)+(1 if abstraction>=2 else 0)
    return LEVELS[min(value,2)]

def difficulty_profile(item):
    return {"difficulty":item.get("difficulty","MEDIUM"),
            "bloom":item.get("bloom","UNDERSTAND"),
            "steps":item.get("steps",1),
            "abstraction":item.get("abstraction",1)}
