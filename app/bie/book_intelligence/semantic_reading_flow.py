class E(ValueError):pass
RANK={"chapter":0,"section":1,"paragraph":2,"figure":2,"table":2,"equation":2,"caption":3}
def validate(nodes):
 if not nodes:return {"passed":True,"violations":()}
 violations=[]
 for i,n in enumerate(nodes):
  if n.get("kind") not in RANK:raise E("kind")
  if n["kind"]=="caption" and (i==0 or nodes[i-1].get("kind") not in {"figure","table","equation"}):violations.append(n.get("id"))
 return {"passed":not violations,"violations":tuple(violations)}
