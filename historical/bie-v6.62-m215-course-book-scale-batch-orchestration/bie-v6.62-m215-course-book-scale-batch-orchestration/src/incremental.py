def affected(changed,nodes):
 a=set(changed); go=True
 while go:
  go=False
  for n in nodes:
   if n["node_id"] not in a and any(x in a for x in n["depends_on"]):
    a.add(n["node_id"]);go=True
 return [n["node_id"] for n in nodes if n["node_id"] in a]
def scope(changed,nodes): return {"changed_nodes":changed,"affected_nodes":affected(changed,nodes)}
