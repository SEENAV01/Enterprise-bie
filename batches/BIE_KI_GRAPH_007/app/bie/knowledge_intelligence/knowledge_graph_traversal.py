class E(ValueError):pass
def traverse(graph,start,max_depth=1,edge_types=None):
 if start not in graph["nodes"] or max_depth<0:raise E("input")
 allowed=set(edge_types) if edge_types else None;seen={start};front={start}
 for _ in range(max_depth):
  nxt=set()
  for e in graph.get("edges",()):
   if allowed is not None and e.get("type") not in allowed:continue
   if e["source"] in front and e["target"] not in seen:nxt.add(e["target"])
  seen|=nxt;front=nxt
 return tuple(sorted(seen))
