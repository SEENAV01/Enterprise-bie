import math

def lesson_boundaries(concepts,max_load=2):
 if not math.isfinite(max_load) or max_load<=0: raise ValueError("load budget")
 out=[]; cur=[]; load=0; topic=None
 for cid,tp,cost in concepts:
  if not cid.strip() or not tp.strip() or not math.isfinite(cost) or cost<0 or cost>max_load: raise ValueError("concept exceeds load budget or has invalid load")
  if cur and (tp!=topic or load+cost>max_load): out.append(tuple(cur)); cur=[]; load=0
  cur.append(cid); load+=cost; topic=tp
 if cur: out.append(tuple(cur))
 return tuple(out)
