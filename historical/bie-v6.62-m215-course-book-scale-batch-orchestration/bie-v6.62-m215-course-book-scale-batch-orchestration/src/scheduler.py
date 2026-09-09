def levels(nodes,order,max_parallel=4):
 by={n["node_id"]:n for n in nodes}; pending=list(order); done=set(); result=[]
 while pending:
  ready=[x for x in pending if all(d in done for d in by[x]["depends_on"])][:max_parallel]
  if not ready: raise ValueError("SCHEDULER_DEADLOCK")
  result.append(ready)
  for x in ready: pending.remove(x);done.add(x)
 return result
