
from collections import deque
class ImpactError(ValueError): pass
def reverse_graph(tasks):
 r={k:[] for k in tasks}
 for t,v in tasks.items():
  for d in v.get("dependencies",[]):
   if d in r:r[d].append(t)
 for k in r:r[k].sort()
 return r
def impact(tasks,changed_task):
 if changed_task not in tasks: raise ImpactError("unknown task")
 rev=reverse_graph(tasks); dist={changed_task:0}; q=deque([changed_task])
 while q:
  n=q.popleft()
  for x in rev[n]:
   if x not in dist: dist[x]=dist[n]+1;q.append(x)
 return [{"task_id":k,"distance":dist[k],"status":tasks[k].get("status")} for k in sorted(dist,key=lambda x:(dist[x],x)) if k!=changed_task]
def invalidation_candidates(tasks,changed_task):
 return [x["task_id"] for x in impact(tasks,changed_task) if x["status"] in {"IMPLEMENTED","UNIT_TESTED","INTEGRATION_TESTED","GOLDEN_TESTED","QA_VERIFIED","ACCEPTED"}]
