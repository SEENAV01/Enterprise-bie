def components(graph):
 nodes=set(graph["nodes"]);adj={n:set() for n in nodes}
 for e in graph.get("edges",()):
  if e["source"] in nodes and e["target"] in nodes:adj[e["source"]].add(e["target"]);adj[e["target"]].add(e["source"])
 out=[]
 while nodes:
  seed=nodes.pop();seen={seed};stack=[seed]
  while stack:
   x=stack.pop()
   for y in adj[x]:
    if y in nodes:nodes.remove(y);seen.add(y);stack.append(y)
  out.append(frozenset(seen))
 return tuple(out)
