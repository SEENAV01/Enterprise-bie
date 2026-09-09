class E(ValueError):pass
def group(op,cs):
 cs=tuple(cs)
 if op not in {"ALL","ANY","NOT"} or not cs or (op=="NOT" and len(cs)!=1):raise E("logic")
 return {"operator":op,"conditions":cs}
def satisfied(g,t):
 v=[bool(t.get(c,False)) for c in g["conditions"]]
 return all(v) if g["operator"]=="ALL" else (any(v) if g["operator"]=="ANY" else not v[0])
