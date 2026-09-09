def impacted(nodes,edges,start):
 if start not in nodes:raise ValueError("unknown node")
 a={n:[] for n in nodes}
 for x,y in edges:
  if x not in a or y not in a:raise ValueError("unknown node")
  a[x].append(y)
 s=set();q=list(a[start])
 while q:
  n=q.pop()
  if n not in s:s.add(n);q+=a[n]
 return tuple(sorted(s))
