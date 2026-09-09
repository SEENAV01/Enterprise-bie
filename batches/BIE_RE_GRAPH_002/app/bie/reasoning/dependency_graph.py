def dependencies(nodes,edges,target):
 if target not in nodes:raise ValueError("unknown target")
 rev={n:[] for n in nodes}
 for a,b in edges:
  if a not in rev or b not in rev:raise ValueError("unknown node")
  rev[b].append(a)
 seen=set();stack=list(rev[target])
 while stack:
  n=stack.pop()
  if n not in seen:seen.add(n);stack.extend(rev[n])
 return tuple(sorted(seen))
