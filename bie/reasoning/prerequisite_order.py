def decide(nodes,edges):
 incoming={n:0 for n in nodes}; adj={n:[] for n in nodes}
 for a,b in edges:
  if a not in incoming or b not in incoming: raise ValueError("unknown node")
  adj[a].append(b); incoming[b]+=1
 q=sorted(n for n in nodes if incoming[n]==0); out=[]
 while q:
  n=q.pop(0); out.append(n)
  for x in sorted(adj[n]):
   incoming[x]-=1
   if incoming[x]==0:q.append(x);q.sort()
 return tuple(out),len(out)==len(nodes)
