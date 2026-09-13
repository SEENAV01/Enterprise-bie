def sequence_lessons(items,edges):
 items=tuple(items); indeg={x:0 for x in items}; adj={x:[] for x in items}
 for a,b in edges:
  if a not in indeg or b not in indeg: raise ValueError("unknown")
  adj[a].append(b); indeg[b]+=1
 ready=sorted(x for x in items if indeg[x]==0); out=[]
 while ready:
  x=ready.pop(0); out.append(x)
  for y in sorted(adj[x]):
   indeg[y]-=1
   if indeg[y]==0: ready.append(y); ready.sort()
 if len(out)!=len(items): raise ValueError("cycle")
 return tuple(out)
