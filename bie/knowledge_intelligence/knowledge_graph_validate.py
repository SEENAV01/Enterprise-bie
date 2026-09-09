class E(ValueError):pass
def validate(graph):
 nodes=graph.get("nodes",{});edges=graph.get("edges",())
 issues=[]
 for i,e in enumerate(edges):
  if e.get("source") not in nodes or e.get("target") not in nodes:issues.append(("dangling",i))
  if e.get("source")==e.get("target"):issues.append(("self_loop",i))
  if not e.get("type"):issues.append(("missing_type",i))
 return {"passed":not issues,"issues":tuple(issues)}
