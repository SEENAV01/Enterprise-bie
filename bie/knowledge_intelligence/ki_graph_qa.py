def evaluate(graph):
 nodes=set(graph.get("nodes",{}));issues=[]
 for i,e in enumerate(graph.get("edges",())):
  if e.get("source") not in nodes or e.get("target") not in nodes:issues.append(("dangling",i))
  if not e.get("anchors"):issues.append(("ungrounded",i))
 orphans=set(nodes)
 for e in graph.get("edges",()):
  orphans.discard(e.get("source"));orphans.discard(e.get("target"))
 return {"passed":not issues,"issues":tuple(issues),"orphans":tuple(sorted(orphans))}
