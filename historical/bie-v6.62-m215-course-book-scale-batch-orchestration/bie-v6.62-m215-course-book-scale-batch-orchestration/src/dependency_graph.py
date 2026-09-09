def topological_order(nodes):
 d={n["node_id"]:0 for n in nodes}; out={n["node_id"]:[] for n in nodes}; by={n["node_id"]:n for n in nodes}
 for n in nodes:
  for x in n["depends_on"]:
   if x not in by: raise ValueError("UNKNOWN_DEPENDENCY")
   d[n["node_id"]]+=1; out[x].append(n["node_id"])
 q=[x for x,v in d.items() if v==0]; order=[]
 while q:
  x=q.pop(0); order.append(x)
  for y in out[x]:
   d[y]-=1
   if d[y]==0:q.append(y)
 if len(order)!=len(nodes):raise ValueError("DEPENDENCY_CYCLE")
 return order
