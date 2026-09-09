def find(graph):
 degree={n:0 for n in graph["nodes"]}
 for e in graph.get("edges",()):
  if e["source"] in degree:degree[e["source"]]+=1
  if e["target"] in degree:degree[e["target"]]+=1
 return tuple(sorted(n for n,d in degree.items() if d==0))
