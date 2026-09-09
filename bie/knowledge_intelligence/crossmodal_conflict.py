class E(ValueError):pass
def detect(items):
 if not items:raise E("items")
 groups={}
 for x in items:groups.setdefault(x["semantic_key"],set()).add(str(x["value"]))
 conflicts={k:tuple(sorted(v)) for k,v in groups.items() if len(v)>1}
 return {"passed":not conflicts,"conflicts":conflicts,"status":"REVIEW" if conflicts else "CLEAR"}
