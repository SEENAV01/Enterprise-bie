def find_cycles(nodes,edges):
 a={n:[] for n in nodes}
 for x,y in edges:
  if x not in a or y not in a: raise ValueError("unknown node")
  a[x].append(y)
 out=[];vis=set();active=set()
 def d(n,path):
  vis.add(n);active.add(n)
  for x in a[n]:
   if x not in vis:d(x,path+[x])
   elif x in active:out.append(tuple(path[path.index(x):]+[x]))
  active.remove(n)
 for n in nodes:
  if n not in vis:d(n,[n])
 return tuple(out)
