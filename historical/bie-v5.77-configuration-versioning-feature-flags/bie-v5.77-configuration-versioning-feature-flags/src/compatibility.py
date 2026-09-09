def compatibility(required,available):
    failures=[]
    for key,value in required.items():
        if available.get(key)!=value:
            failures.append({"key":key,"required":value,
                             "available":available.get(key)})
    return {"compatible":not failures,"failures":failures}
